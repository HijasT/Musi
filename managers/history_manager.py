"""Persistent log of every successful download, keyed by canonical track identity.

Unlike duplicate detection against the output directory (utils.track_checker),
this survives the audio file being moved, renamed outside the app, or deleted —
so a track can be flagged as "downloaded before" even if it's no longer on disk.
"""

import json
import os
from datetime import datetime, timezone
from typing import Optional

from constants import HISTORY_FILE
from utils.track_checker import track_key
from utils.filename_match import normalize_match_key
from utils.logger import log_error


def load_history() -> dict:
    """Load the download history dict, keyed by canonical track key."""
    if not os.path.exists(HISTORY_FILE):
        return {}
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {}
            data = json.loads(content)
            return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError) as e:
        log_error(f"Failed to load download history: {e}")
        return {}


def save_history(history: dict) -> None:
    try:
        os.makedirs(os.path.dirname(HISTORY_FILE) or ".", exist_ok=True)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
    except OSError as e:
        log_error(f"Failed to save download history: {e}")


def log_download(artist: str, track: str, file_path: Optional[str] = None,
                  playlist: Optional[str] = None, audio_format: Optional[str] = None) -> None:
    """Record a successful audio download. Safe to call repeatedly for the same track."""
    if not artist or not track:
        return

    key = track_key({"artist": artist, "track": track})
    history = load_history()
    history[key] = {
        "kind": "audio",
        "artist": artist,
        "track": track,
        "file_path": file_path,
        "playlist": playlist,
        "audio_format": audio_format,
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
    }
    save_history(history)


def log_video_download(title: str, url: str, file_path: Optional[str] = None) -> None:
    """Record a successful video download. Keyed by URL, since videos don't
    have a canonical artist/track identity the way audio downloads do."""
    if not url:
        return

    key = "video:" + normalize_match_key(url)
    history = load_history()
    history[key] = {
        "kind": "video",
        "title": title or url,
        "url": url,
        "file_path": file_path,
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
    }
    save_history(history)


def get_history_entry(artist: str, track: str) -> Optional[dict]:
    """Return the history record for a track, or None if it was never downloaded."""
    key = track_key({"artist": artist, "track": track})
    return load_history().get(key)


def has_been_downloaded(artist: str, track: str) -> bool:
    return get_history_entry(artist, track) is not None


def get_stats() -> dict:
    """Return {'audio_count': int, 'video_count': int} from the download history.

    Entries without a 'kind' field are legacy audio downloads logged before
    this field existed, and are counted as audio.
    """
    history = load_history()
    audio_count = 0
    video_count = 0
    for entry in history.values():
        if entry.get("kind") == "video":
            video_count += 1
        else:
            audio_count += 1
    return {"audio_count": audio_count, "video_count": video_count}
