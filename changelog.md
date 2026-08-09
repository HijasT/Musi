# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Changed
- **Renamed to Chaos Media Downloader** (was Musi): the GitHub repo moved from `HijasT/Musi` to `HijasT/ChaosMD`, and every user-facing string, internal identifier, and build artifact was updated to match — window/taskbar title, About dialog, macOS support-folder path, User-Agent strings, PyInstaller output (`ChaosMD.exe`/`.app`/release archives), and `constants.GITHUB_REPO`. The logo, theme, and all functionality are unchanged.

### Added
- **In-app update checker**: on every launch, the app checks GitHub Releases in the background (no startup delay) and prompts to open the download page if a newer version is available. `constants.APP_VERSION` is now the single source of truth for the running version (title bar badge, About dialog, and the checker all read from it) — bump it alongside each tagged release.
- **Favorites**: save a link or search under a name for one-click re-download later, without re-typing or re-navigating (`managers/favorites_manager.py`, `data/favorites.json`). Available from the CLI Downloads menu and a new Favorites section in the GUI's YouTube view; downloads offer to save themselves as a favorite afterward.
- **Video downloads**: a new standalone mode downloads the actual video (merged best video + audio, mp4, with subtitles/thumbnail/metadata embedded) from YouTube, TikTok, Instagram, Twitter/X, Reddit, Twitch, and hundreds of other yt-dlp-supported sites — `downloader/video_downloader.py`, a new `video_output_dir` setting (default `videos`), the CLI's "Download video from a link" option, and a "Download Video" section in the GUI's YouTube view. Kept separate from the audio DownloadQueue since video isn't an audio-format/metadata-embedding operation.

## [1.3.0] - 2026-08-09

### Added
- **New app logo**: a twin-reel mark on the "Tape Deck" charcoal-and-green palette, replacing the old glossy blue music-note icon (`gui/resources/icons/app/`).
- **320kbps downloads**: new `audio_bitrate` config setting (default `320k`) applied via yt-dlp's `--audio-quality` across every download path. Editable from Settings or the CLI's "Choose audio bitrate" tool.
- **ffmpeg-based library converter**: `tools/convert_audio.py` bulk-converts already-downloaded files to a chosen format/bitrate, from the CLI Tools menu or Settings → Library Maintenance → "Convert Library".
- **Persistent download history**: `managers/history_manager.py` logs every successful download by canonical artist/track key, independent of the file's continued existence on disk. Playlist selection now marks tracks "(previously downloaded)", and "download all pending" flows confirm before re-downloading them.
- **Auto-fetched lyrics**: plain lyrics pulled from lrclib.net (no API key) and embedded per-format (USLT for MP3/WAV, `LYRICS` for FLAC/Vorbis/Opus, `©lyr` for M4A). Toggle via the new `enable_lyrics_fetch` setting (default on).

### Fixed
- Download queue status chips (`gui/views/downloads_view.py`) could render at the wrong position/size, or lose their background styling entirely, due to relying on Qt's global stylesheet cascade for a widget reparented into a table cell after the app stylesheet was already applied. Chips now use inline styling set directly on the label and are updated in place rather than replaced, which also avoids orphaned widgets being left behind in the table.

## [1.0.0] - 2026-08-09 (Musi fork)

### Added
- **Musi rebrand**: forked from [Harmoni](https://github.com/Ssenseii/harmoni) and renamed throughout the GUI package and entry point (window title, About dialog, welcome screen, taskbar app ID, macOS support-folder path).
- **"Tape Deck" GUI redesign**: new charcoal-black theme with a green accent (`gui/styles.py`), replacing the original dark-purple theme. Chip-style status badges (Queued/Downloading/Done/Failed) in the download queue view.
- **Auto-redownload corrupted files**: library cleanup (`tools/library_cleanup.py`) now re-queues a redownload for each corrupted/empty file it removes, instead of only deleting it. Controlled by the new `auto_redownload_corrupted` config setting (default on), toggleable from the CLI Config menu or the GUI Settings view's new "Library Maintenance" section.

### Why
- The original theme read as generic/AI-templated; the redesign gives the app a distinct visual identity while keeping the existing layout and widgets intact.
- Corrupted files silently disappearing from the library (previous behavior) meant tracks had to be manually re-added and re-downloaded; auto-redownload closes that loop automatically.

## [1.2.0] - 2026-07-30

### Added
- **Custom yt-dlp / ffmpeg arguments**: You can now pass extra CLI flags straight through to yt-dlp and ffmpeg for every download:
  - New `ytdlp_extra_args` and `ffmpeg_extra_args` config fields (ffmpeg args are forwarded via yt-dlp's `--postprocessor-args`)
  - New "Extra yt-dlp arguments" / "Extra ffmpeg arguments" fields in the GUI Settings view, under Download Settings
  - Editable from the CLI config menu like any other setting
  - Applied consistently across all download paths: track/batch downloads, retries, and direct link/playlist downloads
- **Disconnect button for Spotify**: The Spotify view now has a "Disconnect" button next to Connect, so you can clear the cached token and re-auth without digging through files.

### Fixed
- **Duplicate-detection and metadata matching for special/reserved characters**: Filenames with characters yt-dlp sanitizes (`: * / \ < > | " ?`) or full-width unicode variants no longer cause tracks to be re-downloaded or fail metadata embedding. Matching is now done via a normalized key (`utils/filename_match.py`) instead of exact/prefix string comparison, in `downloader/metadata.py` and `utils/track_checker.py`.
- **Bundled yt-dlp binary was being stripped on macOS/Linux builds**, breaking every download on those platforms. The build workflow and `build-macos.sh` no longer strip it.

### Why
- Passing custom flags was the most requested missing feature: without something like `--cookies cookies.txt`, large playlist downloads get rate-limited/timed out by YouTube. Power users can now also tweak ffmpeg output (e.g. sample rate) without touching code.
- The filename-matching fix prevents silent re-downloads/duplicate work for tracks whose titles contain characters that get sanitized differently across yt-dlp versions/platforms.
- The macOS/Linux build fix was a release blocker — every download failed post-build until yt-dlp was no longer stripped.

### Compatibility
- Fully backward compatible with older `config.json` files. Missing keys are backfilled with empty defaults on load, so existing configs keep working unchanged and no extra arguments are applied unless explicitly set.

## [1.1.0] - 2026-03-03

### Added
- **yt-dlp Update Checker & Installer**: Implemented a comprehensive update system for yt-dlp with:
  - Automatic update detection through the update checker module
  - In-app notifications to alert users when updates are available
  - One-click installer for seamless yt-dlp updates
  - New `ytdlp_updater.py` worker module handling update logic in GUI thread

### Changed
- **Settings View**: Now automatically reloads configuration on save and updates the UI to reflect changes immediately
- **Spotify Integration**: Refactored token expiration checking to use the TokenManager, improving code maintainability and centralizing token lifecycle management
- **Main Window**: Updated to support the new yt-dlp update checker integration

### Why
These changes were made to improve user experience and code quality:
1. Users can now keep yt-dlp updated without manual intervention, ensuring access to the latest features and bug fixes
2. Settings changes take immediate effect without requiring app restart (I think you'll have to reload the app after installing yt-dlp because visually it shows not installed)
3. Centralized token management through TokenManager reduces duplication and potential bugs in token handling across different parts of the application
4. when you open the app, there will be some quick cli openings which is a bit scary but don't worry, it's just small scripts to check for things if they are there or not.

## [1.0.0] - 2026-01-01

### Added
- Initial stable release of Harmoni
- GUI version 1.0.0 with core features
- Initial yt-dlp update checker foundation
