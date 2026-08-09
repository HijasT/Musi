# App version — single source of truth, kept in sync with the GitHub release
# tags (e.g. "1.3.0" here matches release tag "v1.3.0"). Bump this alongside
# each tagged release so the in-app update checker compares against itself.
APP_VERSION = "1.3.0"
GITHUB_REPO = "HijasT/ChaosMD"

PYTHON_DEPENDENCIES = [
    "psutil",
    "colorama",
    "mutagen",
    "schedule",
    "questionary",
]

SYSTEM_DEPENDENCIES = [
    "ffmpeg",
]

# Audio Related

VALID_AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"}

AUDIO_BITRATE_OPTIONS = {
    "64k": "Very low quality (speech/podcasts)",
    "96k": "Low quality (voice focus)",
    "128k": "Medium quality (most music)",
    "192k": "Good quality (balanced size)",
    "256k": "High quality",
    "320k": "Best quality (larger file size)"
}


# Files

FAILED_FILE = "data/failed_downloads.json"
PROGRESS_FILE = "data/download_progress.json"
HISTORY_FILE = "data/download_history.json"
FAVORITES_FILE = "data/favorites.json"
LOG_FILE = "app.log"