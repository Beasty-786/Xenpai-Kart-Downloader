import ast
import argparse
import os
import plistlib
import shutil
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from app.config.constants import VERSION, YEAR, AUTHOR, DESKTOP_ID

MACOS_DOCUMENT_TYPES = [
    {"name": "种子文件", "extensions": ["torrent"], "icon": "torrent"},
    {"name": "M3U8 播放列表", "extensions": ["m3u8", "m3u"], "icon": "m3u8"},
    {"name": "DASH 清单", "extensions": ["mpd"], "icon": "m3u8"},
]

EXCLUDED_PACKS = {"jack_yao"}

EXTRA_INCLUDE_PACKAGES = []
PLATFORM_INCLUDE_PACKAGES = {
    "win32": ["winrt"],
}
EXTRA_INCLUDE_MODULES = [
    "app.view.dialogs.edit_task",
    "concurrent.futures",
    "email.header",
    "html.entities",
    "html.parser",
    "http.client",
    "http.cookiejar",
    "http.cookies",
    "http.server",
    "urllib.error",
    "urllib.response",
    "xml.etree.ElementTree",
]


def findImports(files: Iterable[Path]) -> tuple[set[str], set[str]]:
    appModules: set[str] = set()
    thirdParty: set[str] = set()
    for source in files:
        tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    dotted = alias.name
                    top = dotted.split(".")[0]
                    if top == "app":
                        base = Path(*dotted.split("."))
                        if base.with_suffix(".py").is_file() or (base / "__init__.py").is_file():
                            appModules.add(dotted)
                    elif top and top not in sys.stdlib_module_names:
                        thirdParty.add(top)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                module = node.module
                top = module.split(".")[0]

                if top == "app":
                    base = Path(*module.split("."))
                    if base.with_suffix(".py").is_file() or (base / "__init__.py").is_file():
                        appModules.add(module)
                elif top and top not in sys.stdlib_module_names:
                    thirdParty.add(top)

                for alias in node.names:
                    dotted = f"{module}.{alias.name}"
                    if top == "app":
                        base = Path(*dotted.split("."))
                        if base.with_suffix(".py").is_file() or (base / "__init__.py").is_file():
                            appModules.add(dotted)

    return appModules, thirdParty


def findIncludes() -> tuple[list[str], list[str]]:
    featureFiles = (path for pack in findPacks() for path in pack.rglob("*.py"))
    featureModules, featurePackages = findImports(featureFiles)
    appModules, appPackages = findImports((REPO / "app").rglob("*.py"))

    featuresDir = REPO / "features"
    internalPackages = {featuresDir.name} | {item.name for item in featuresDir.iterdir() if item.is_dir()}

    packages = (featurePackages - appPackages - internalPackages) | set(EXTRA_INCLUDE_PACKAGES)
    packages |= set(PLATFORM_INCLUDE_PACKAGES.get(sys.platform, []))

    modules = {
        module
        for module in featureModules - appModules
        if not (Path(*module.split(".")) / "__init__.py").is_file()
    } | set(EXTRA_INCLUDE_MODULES)

    return sorted(packages), sorted(modules)


def buildArgs(onefile: bool = False) -> list[str]:
    includePackages, includeModules = findIncludes()
    includeArgs = [
        *[f"--include-package={package}" for package in includePackages],
        *[f"--include-module={module}" for module in includeModules],
    ]

    nuitka = f'"{sys.executable}" -m nuitka'

    if sys.platform == "win32":
        args = [
            nuitka,
            '--onefile' if onefile else '--standalone',
            '--windows-console-mode=attach',
            '--plugin-enable=pyside6',
            *includeArgs,
            '--assume-yes-for-downloads',
            '--msvc=latest',
            '--windows-icon-from-ico=app/assets/logo.ico',
            '--include-data-dir=app/assets/file_icons=app/assets/file_icons',
            '--company-name="Dhiraj Kumar Singh"',
            '--product-name="Xenpai Kart Downloader"',
            f'--file-version={VERSION}',
            f'--product-version={VERSION}',
            '--file-description="Xenpai Kart Downloader"',
            f'--copyright="Copyright(C) {YEAR} {AUTHOR}"',
            '--output-dir=build/standalone' if onefile else '--output-dir=dist',
        ]
        if onefile:
            args.extend([
                *[
                    f'--include-package={pack.name}'
                    for pack in findPacks()
                ],
                '--include-data-dir=build/onefile_features=features',
                f'--output-filename=Xenpai-Kart-Downloader-v{VERSION}-Standalone.exe',
            ])
        args.append('Xenpai-Kart-Downloader.py')
        return args

    if sys.platform == "darwin":
        return [
            nuitka,
            '--standalone',
            '--plugin-enable=pyside6',
            *includeArgs,
            '--static-libpython=no',
            "--macos-create-app-bundle",
            "--assume-yes-for-downloads",
            "--macos-app-mode=gui",
            f"--macos-app-version={VERSION}",
            "--macos-app-icon=app/assets/logo.icns",
            f'--copyright="Copyright(C) {YEAR} {AUTHOR}"',
            '--output-dir=dist',
            'Xenpai-Kart-Downloader.py',
        ]

    return [
        nuitka,
        '--standalone',
        '--plugin-enable=pyside6',
        *includeArgs,
        '--include-qt-plugins=platforms',
        '--include-module=PySide6.QtDBus',
        '--assume-yes-for-downloads',
        '--linux-icon=app/assets/logo.png',
        '--output-dir=dist',
        'Xenpai-Kart-Downloader.py',
    ]


def findPacks() -> list[Path]:
    featuresDir = REPO / "features"
    if not featuresDir.is_dir():
        raise FileNotFoundError(f"features directory not found: {featuresDir}")

    return sorted(
        (
            item
            for item in featuresDir.iterdir()
            if item.is_dir()
            and item.name not in EXCLUDED_PACKS
            and (item / "manifest.toml").is_file()
        ),
        key=lambda item: item.name,
    )


def copyPacks() -> None:
    packs = findPacks()
    if not packs:
        raise RuntimeError("No feature packs were found to copy.")

    if sys.platform == "darwin":
        targetRoot = Path("dist") / "Xenpai-Kart-Downloader.app" / "Contents" / "MacOS" / "features"
    else:
        targetRoot = Path("dist") / "Xenpai-Kart-Downloader.dist" / "features"

    if not targetRoot.parent.exists():
        raise FileNotFoundError(f"dist directory does not exist: {targetRoot.parent}")

    if targetRoot.exists():
        shutil.rmtree(targetRoot)
    targetRoot.mkdir(parents=True, exist_ok=True)

    ignorePatterns = shutil.ignore_patterns("*.svg", "*.qrc")
    for source in packs:
        shutil.copytree(source, targetRoot / source.name, ignore=ignorePatterns)

    print(f"Copied feature packs to {targetRoot}: {[p.name for p in packs]}")


def prepareOnefilePacks() -> None:
    """Stage manifests while Nuitka embeds the feature-pack Python packages."""
    targetRoot = REPO / "build" / "onefile_features"
    if targetRoot.exists():
        shutil.rmtree(targetRoot)
    targetRoot.mkdir(parents=True)

    for sourceRoot in findPacks():
        targetPack = targetRoot / sourceRoot.name
        targetPack.mkdir()
        shutil.copy2(sourceRoot / "manifest.toml", targetPack / "manifest.toml")

    print(f"Prepared onefile feature packs in {targetRoot}")


def patchInfoPlist() -> None:
    appBundle = Path("dist") / "Xenpai-Kart-Downloader.app"
    plistPath = appBundle / "Contents" / "Info.plist"
    resourcesDir = appBundle / "Contents" / "Resources"
    resourcesDir.mkdir(parents=True, exist_ok=True)

    fileIconsDir = REPO / "app" / "assets" / "file_icons"
    documentTypes = []
    for entry in MACOS_DOCUMENT_TYPES:
        shutil.copy(fileIconsDir / f"{entry['icon']}.icns", resourcesDir / f"{entry['icon']}.icns")
        documentTypes.append(
            {
                "CFBundleTypeName": entry["name"],
                "CFBundleTypeRole": "Viewer",
                "CFBundleTypeExtensions": entry["extensions"],
                "CFBundleTypeIconFile": f"{entry['icon']}.icns",
                "LSHandlerRank": "Alternate",
            }
        )

    with open(plistPath, "rb") as f:
        plist = plistlib.load(f)
    plist["CFBundleDocumentTypes"] = documentTypes
    plist["CFBundleIdentifier"] = DESKTOP_ID
    plist["CFBundleURLTypes"] = [{
        "CFBundleURLName": DESKTOP_ID,
        "CFBundleURLSchemes": ["xenpaikartdownloader"],
    }]
    with open(plistPath, "wb") as f:
        plistlib.dump(plist, f)

    print(f"Patched Info.plist with {len(documentTypes)} document types + URL scheme")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--onefile",
        action="store_true",
        help="Build a single portable Windows executable with embedded feature packs.",
    )
    options = parser.parse_args()

    os.chdir(REPO)

    if options.onefile:
        if sys.platform != "win32":
            parser.error("--onefile is currently supported only on Windows")
        prepareOnefilePacks()

    args = buildArgs(onefile=options.onefile)
    command = ' '.join(args)

    print(command)
    env = os.environ.copy()
    if options.onefile:
        featurePath = str(REPO / "features")
        env["PYTHONPATH"] = os.pathsep.join(
            value for value in (featurePath, env.get("PYTHONPATH", "")) if value
        )

    result = subprocess.run(command, shell=True, env=env)
    if result.returncode != 0:
        return result.returncode

    if options.onefile:
        filename = f"Xenpai-Kart-Downloader-v{VERSION}-Standalone.exe"
        source = REPO / "build" / "standalone" / filename
        target = REPO / "dist" / filename
        if not source.is_file():
            raise FileNotFoundError(f"Standalone executable was not created: {source}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        print(f"Copied standalone executable to {target}")
    else:
        copyPacks()

    if sys.platform == "darwin":
        patchInfoPlist()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
