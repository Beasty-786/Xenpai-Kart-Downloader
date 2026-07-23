from __future__ import annotations

import shutil
import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from app.config.constants import LATEST_EXTENSION_VERSION


def archive(source: Path, destination: Path) -> None:
    if not (source / "manifest.json").is_file():
        raise FileNotFoundError(f"Extension build is missing: {source}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(destination, "w", compression=ZIP_DEFLATED, compresslevel=9) as output:
        for path in sorted(source.rglob("*")):
            if path.is_file():
                output.write(path, path.relative_to(source).as_posix())


def main() -> int:
    browser_root = REPO / "browser_extension"
    dist = REPO / "dist"
    assets = REPO / "app" / "assets"

    chromium_release = (
        dist
        / f"Xenpai-Kart-Downloader-Chromium-v{LATEST_EXTENSION_VERSION}.zip"
    )
    firefox_release = (
        dist
        / f"Xenpai-Kart-Downloader-Firefox-v{LATEST_EXTENSION_VERSION}.xpi"
    )

    archive(browser_root / "chromium", chromium_release)
    archive(browser_root / "firefox", firefox_release)
    shutil.copy2(chromium_release, assets / "chrome_extension.zip")

    print(chromium_release)
    print(firefox_release)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
