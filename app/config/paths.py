import shutil
import sys
from pathlib import Path

from PySide6.QtCore import QStandardPaths

from app.platform.android import IS_ANDROID

executableDir = (
    Path(sys.executable).resolve().parent
    if "__compiled__" in globals()
    else Path(".")
)

APP_DATA_DIR: str = (
    f"{QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)}/XenpaiKartDownloader"
    if IS_ANDROID
    else str(executableDir / "XenpaiKartDownloader")
    if (executableDir / "XenpaiKartDownloader").is_dir()
    else f"{QStandardPaths.writableLocation(QStandardPaths.StandardLocation.GenericDataLocation)}/XenpaiKartDownloader"
)

# In onefile builds, bundled data is extracted beside compiled modules while
# sys.executable continues to point at the original portable EXE.
_moduleRoot = Path(__file__).resolve().parents[2]
bundledResourceDir = (
    _moduleRoot if (_moduleRoot / "features").is_dir() else executableDir
)

PORTABLE_PATH = executableDir / "XenpaiKartDownloader"
USER_PATH = Path(QStandardPaths.writableLocation(
    QStandardPaths.StandardLocation.GenericDataLocation
)) / "XenpaiKartDownloader"

def isPortable() -> bool:
    return APP_DATA_DIR == str(PORTABLE_PATH)


def migrate(target: Path) -> None:
    from loguru import logger
    logger.remove()
    source = Path(APP_DATA_DIR)
    target.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target, dirs_exist_ok=True)
    if isPortable():
        source.rename(source.with_suffix(".bak"))
