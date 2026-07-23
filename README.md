# Xenpai Kart Downloader

Xenpai Kart Downloader is an English-only Windows download manager published by
**Dhiraj Kumar Singh**.

It supports HTTP/HTTPS downloads, Magnet and BitTorrent links, FTP, M3U8,
MPEG-DASH, eD2k, GitHub releases, Hugging Face files, and media downloads
through yt-dlp.

## Branding

- Application name: **Xenpai Kart Downloader**
- Publisher: **Dhiraj Kumar Singh**
- Windows executable: `Xenpai-Kart-Downloader.exe`
- Application data: `%LOCALAPPDATA%\XenpaiKartDownloader`
- Interface and installer language: English only

## Development

The project uses Python 3.11 and `uv`.

```powershell
uv sync
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe scripts\deploy.py
```

The Windows installer is built with Inno Setup:

```powershell
& "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe" `
  "scripts\Xenpai-Kart-Downloader.iss"
```

## Releases and updates

Every branded release keeps the application name **Xenpai Kart Downloader** and
the same installer `AppId`. Only the semantic version changes. For example:

`Xenpai-Kart-Downloader-v4.1.2-Windows-Setup.exe`

Upstream Ghost Downloader automatic updates are intentionally disabled because
installing an upstream binary would replace the Xenpai name and logo. New
versions must be rebuilt and published from this repository. See
[UPDATE_POLICY.md](UPDATE_POLICY.md).

## License and attribution

This project is derived from
[XiaoYouChR/Ghost-Downloader-3](https://github.com/XiaoYouChR/Ghost-Downloader-3)
and remains licensed under the GNU General Public License v3.0. See
[LICENSE](LICENSE) and [BRANDING.md](BRANDING.md).
