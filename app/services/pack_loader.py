from __future__ import annotations

import importlib
import importlib.util
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from app.models.pack import FeaturePack


@dataclass(frozen=True)
class PackManifest:
    name: str
    className: str
    moduleName: str
    entryPath: Path
    folder: Path
    dependencies: tuple[str, ...]

    @classmethod
    def fromDir(cls, packDir: Path) -> PackManifest | None:
        manifestPath = packDir / "manifest.toml"
        if not manifestPath.exists():
            logger.warning("Feature pack is missing manifest.toml: {}", packDir)
            return None

        try:
            raw = tomllib.loads(manifestPath.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning("Unable to read manifest {}: {}", manifestPath, repr(e))
            return None

        packSection = raw.get("pack")
        if not isinstance(packSection, dict):
            logger.warning("Manifest is missing its [pack] section: {}", manifestPath)
            return None

        entry = packSection.get("entry", "pack.py")
        if not isinstance(entry, str) or not entry.strip():
            logger.warning("Manifest entry is invalid: {}", manifestPath)
            return None

        entryPath = packDir / entry
        moduleName = f"{packDir.name}.{Path(entry).with_suffix('').as_posix().replace('/', '.')}"
        if not entryPath.exists() and importlib.util.find_spec(moduleName) is None:
            logger.warning("Feature pack entry does not exist: {}", packDir / entry)
            return None

        className = packSection.get("class")
        if not isinstance(className, str) or not className.strip():
            logger.warning("Manifest is missing its class field: {}", manifestPath)
            return None

        deps = packSection.get("dependencies", [])
        if not isinstance(deps, list) or any(
            not isinstance(d, str) or not d for d in deps
        ):
            logger.warning("Manifest dependencies are invalid: {}", manifestPath)
            return None

        return cls(
            name=packDir.name,
            className=className,
            moduleName=moduleName,
            entryPath=entryPath,
            folder=packDir,
            dependencies=tuple(deps),
        )


def loadPacks(featuresDir: Path, services=None) -> list[FeaturePack]:
    if not featuresDir.exists():
        logger.warning("Feature-pack directory does not exist: {}", featuresDir)
        return []

    manifests = [
        m for p in sorted(featuresDir.iterdir())
        if p.is_dir() and not p.name.startswith((".", "__"))
        if (m := PackManifest.fromDir(p)) is not None
    ]
    ordered = orderedByDependency(manifests)
    return [pack for m in ordered if (pack := loadManifest(m, services)) is not None]


def orderedByDependency(manifests: list[PackManifest]) -> list[PackManifest]:
    byName: dict[str, PackManifest] = {m.name: m for m in manifests}
    visiting: list[str] = []
    visited: set[str] = set()
    ordered: list[PackManifest] = []
    skipped: set[str] = set()

    def visit(name: str):
        if name in visited:
            return
        if name in skipped:
            raise ValueError(f"A feature pack required by {name} was skipped")
        if name in visiting:
            cycle = visiting[visiting.index(name):] + [name]
            raise ValueError(f"Circular dependency: {' -> '.join(cycle)}")

        visiting.append(name)
        for dep in byName[name].dependencies:
            if dep not in byName:
                raise ValueError(f"{name} requires missing feature pack: {dep}")
            visit(dep)
        visiting.pop()
        visited.add(name)
        ordered.append(byName[name])

    for m in manifests:
        try:
            visit(m.name)
        except Exception as e:
            skipped.add(m.name)
            visiting.clear()
            logger.opt(exception=e).error("Skipping feature pack {}", m.name)

    return [m for m in ordered if m.name not in skipped]


def loadManifest(manifest: PackManifest, services=None) -> FeaturePack | None:
    moduleName = manifest.moduleName
    try:
        module = importlib.import_module(moduleName)

        PackClass = getattr(module, manifest.className, None)
        if PackClass is None:
            logger.warning("Class {} was not found in {}", manifest.className, moduleName)
            return None

        pack = PackClass(services)
        logger.success("Loaded feature pack: {}", manifest.name)
        return pack

    except Exception as e:
        logger.opt(exception=e).error("Failed to load feature pack: {}", manifest.name)
        return None
