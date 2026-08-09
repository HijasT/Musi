"""Shared duplicate-detection helper for GUI queue-add flows.

Filters out tracks that already exist on disk, and confirms with the user
before re-queuing tracks that were downloaded before (per the persistent
download history) but are missing from the output directory.
"""

import os
from typing import Optional

from PySide6.QtWidgets import QWidget, QMessageBox

from utils.track_checker import existing_track_keys_in_dir, track_key


def _dest_dir(config: dict, playlist_override: Optional[str], track: dict) -> str:
    output_dir = config.get("output_dir", "music")
    playlist = playlist_override if playlist_override is not None else track.get("playlist")
    if playlist:
        return os.path.join(output_dir, str(playlist).replace("/", "-").strip())
    return output_dir


def filter_new_tracks(parent: QWidget, config: dict, tracks: list, playlist: Optional[str] = None) -> list:
    """Return the subset of `tracks` that should actually be queued.

    - Tracks whose file already exists in the destination folder are skipped silently.
    - Tracks found in download history but missing from disk trigger a single
      confirmation dialog for the whole batch; declining excludes them.
    """
    if not tracks:
        return []

    try:
        from managers.history_manager import has_been_downloaded
    except Exception:
        has_been_downloaded = None

    existing_keys_by_dir: dict[str, set] = {}
    new_tracks = []
    missing_from_history = []

    for t in tracks:
        dest_dir = _dest_dir(config, playlist, t)
        if dest_dir not in existing_keys_by_dir:
            existing_keys_by_dir[dest_dir] = existing_track_keys_in_dir(dest_dir)
        existing_keys = existing_keys_by_dir[dest_dir]

        key = track_key(t)
        if key in existing_keys:
            continue
        if has_been_downloaded and has_been_downloaded(t.get("artist", ""), t.get("track", "")):
            missing_from_history.append(t)
        else:
            new_tracks.append(t)

    if missing_from_history:
        reply = QMessageBox.question(
            parent,
            "Previously Downloaded",
            f"{len(missing_from_history)} track(s) were downloaded before but are missing "
            "from your library. Re-download them too?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            new_tracks.extend(missing_from_history)

    return new_tracks
