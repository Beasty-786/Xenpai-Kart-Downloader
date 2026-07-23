from unittest.mock import patch

from app.update import RELEASE_API, assetScore


def test_release_feed_is_xenpai_repository():
    assert RELEASE_API == (
        "https://api.github.com/repos/"
        "Beasty-786/Xenpai-Kart-Downloader/releases/latest"
    )


@patch("app.platform.windows.isLessThanWin10", return_value=False)
@patch("platform.machine", return_value="AMD64")
@patch("sys.platform", "win32")
def test_windows_installer_without_architecture_suffix_is_selected(
    _machine, _windows_version,
):
    name = "Xenpai-Kart-Downloader-v4.1.2-Windows-Setup.exe"
    assert assetScore(name) >= 0


@patch("app.platform.windows.isLessThanWin10", return_value=False)
@patch("platform.machine", return_value="AMD64")
@patch("sys.platform", "win32")
def test_upstream_ghost_asset_is_rejected(_machine, _windows_version):
    assert assetScore("Ghost-Downloader-v9.9.9-Windows-x86_64-Setup.exe") == -1
