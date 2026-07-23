# Xenpai Update Policy

Use this checklist for every Xenpai Kart Downloader update:

1. Review and integrate the desired upstream changes.
2. Preserve the Xenpai name, publisher, logo, application-data directory,
   protocol identifiers, and installer `AppId`.
3. Keep the application and installer English-only.
4. Keep the desktop update feed restricted to this Xenpai repository.
5. Increment the version in the application and installer.
6. Regenerate resources, run the complete test suite, and perform a Windows
   launch/download smoke test.
7. Build the portable application and the English-only Inno Setup installer.
8. Build the English-only Chromium and Firefox extension packages using the
   Xenpai name, logo, version, and URL scheme.
9. Name the installer
   `Xenpai-Kart-Downloader-v<version>-Windows-Setup.exe`.
10. Commit the source changes, push them to this repository, and push the
    matching `v<version>` tag so GitHub publishes all three release files.

The stable installer `AppId` is:

`{D894EDBB-DD87-435B-989C-6EE64995B307}`

Changing that identifier would make Windows treat an update as a separate
application, so it must remain unchanged.
