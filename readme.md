
![Musi icon](gui/resources/icons/app/app_icon.ico)
# Musi

A Python tool for downloading music from Spotify and YouTube using **yt-dlp**. Available as a standalone executable, desktop GUI application, or command-line interface.

Musi is a fork of [Harmoni](https://github.com/Ssenseii/harmoni) by [Ssenseii](https://github.com/Ssenseii), redesigned with a new dark "Tape Deck" interface (charcoal-black with a green accent, replacing the original purple theme) and extended with new features. All credit for the original project goes to its author — see [LICENSE](LICENSE) for the MIT terms this fork keeps.

## What's different from Harmoni

- **Redesigned GUI** — a charcoal-black "Tape Deck" theme with a green accent, condensed display type, and chip-style status badges in the download queue, replacing the original dark-purple interface.
- **Auto-redownload corrupted files** — library cleanup no longer just deletes broken/empty audio files; it automatically re-queues a redownload for each one (toggle via `auto_redownload_corrupted` in Settings or `config.json`).

See [changelog.md](changelog.md) for the full history inherited from Harmoni.

## Features

- **Desktop GUI** - Modern graphical interface with drag-and-drop Exportify support
- **Spotify Integration** - Download from your playlists and liked songs via OAuth
- **YouTube Downloads** - Download from links or search by artist/song
- **Batch Downloads** - Download entire playlists with concurrent processing
- **Exportify Support** - Import playlists from CSV exports (easiest method!)
- **Metadata Embedding** - Automatic ID3 tagging for MP3 files
- **Library Management** - Duplicate detection, cleanup (with auto-redownload), and organization

## Installation Options

### Option 1: Standalone Executable (Easiest)

Download from the [Releases](https://github.com/HijasT/Musi/releases) page:

- **Windows**: `Musi.exe` — double-click to run
- **macOS**: `Musi-macos-arm64.dmg` (Apple Silicon) — open the DMG and drag Musi to Applications

No Python installation required. FFmpeg is bundled.

See [Standalone Guide](docs/guides/standalone.md) for details.

### Option 2: Python Installation

```bash
# Clone and install
git clone https://github.com/HijasT/Musi.git
cd Musi
pip install -r requirements.txt

# Run the GUI
python gui_main.py

# Or run the CLI
python main.py
```

### Option 3: Docker

```bash
docker compose build
docker compose run --rm --service-ports harmoni
```

### Option 4: Build macOS from Source

On any Mac with Python 3.12+ and Homebrew:

```bash
chmod +x build-macos.sh
./build-macos.sh
```

This produces a `Musi-macos-<arch>.dmg` with ffmpeg bundled.

## Quick Start

### GUI (Recommended)

The easiest way to download your Spotify music:

1. Launch Musi (exe, app, or `python gui_main.py`)
2. Go to [exportify.net](https://exportify.net) and log in with Spotify
3. Export your playlists as CSV files
4. Drag and drop the CSV into Musi

No Spotify API setup required!

### Command Line

```bash
python main.py
# or
./start.sh
```

See [CLI Guide](docs/guides/cli.md) for all available commands.

## Requirements

- **Standalone EXE/DMG**: None (ffmpeg bundled)
- **Python version**: Python 3.9+ and ffmpeg

## Documentation

See the [docs/](docs/) folder for detailed guides:

- [Installation Guide](docs/guides/installation.md) - Full setup instructions
- [GUI Guide](docs/guides/gui.md) - Using the desktop application
- [CLI Guide](docs/guides/cli.md) - Command-line interface reference
- [Standalone Guide](docs/guides/standalone.md) - Using the executable
- [Spotify Setup](docs/guides/spotify-setup.md) - Connect your Spotify account
- [Configuration](docs/guides/configuration.md) - Settings reference
- [Docker](docs/guides/docker.md) - Container deployment

## License

MIT License - see [LICENSE](LICENSE) for details. Original work Copyright (c) 2025 Ssenseii.

## Disclaimer

This tool is for **personal use only**. Respect copyright laws and YouTube's terms of service.
