"""Saved links/searches for one-click re-download, without re-typing or
re-navigating. A favorite is either a "link" (a YouTube/video URL, downloaded
as-is) or a "search" (an "Artist - Track" style query)."""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from constants import FAVORITES_FILE
from utils.logger import log_error


def load_favorites() -> list:
    """Load saved favorites, oldest first."""
    if not os.path.exists(FAVORITES_FILE):
        return []
    try:
        with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            data = json.loads(content)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError) as e:
        log_error(f"Failed to load favorites: {e}")
        return []


def save_favorites(favorites: list) -> None:
    try:
        os.makedirs(os.path.dirname(FAVORITES_FILE) or ".", exist_ok=True)
        with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
            json.dump(favorites, f, indent=2)
    except OSError as e:
        log_error(f"Failed to save favorites: {e}")


def add_favorite(name: str, value: str, kind: str) -> Optional[dict]:
    """Add a favorite. kind is 'link' or 'search'. Returns None if a favorite
    with the same value+kind already exists (still updates its name)."""
    name = (name or "").strip()
    value = (value or "").strip()
    if not name or not value or kind not in ("link", "search"):
        return None

    favorites = load_favorites()
    for fav in favorites:
        if fav.get("value") == value and fav.get("kind") == kind:
            fav["name"] = name
            save_favorites(favorites)
            return None

    record = {
        "id": str(uuid.uuid4()),
        "name": name,
        "value": value,
        "kind": kind,
        "added_at": datetime.now(timezone.utc).isoformat(),
    }
    favorites.append(record)
    save_favorites(favorites)
    return record


def remove_favorite(favorite_id: str) -> bool:
    favorites = load_favorites()
    remaining = [f for f in favorites if f.get("id") != favorite_id]
    if len(remaining) == len(favorites):
        return False
    save_favorites(remaining)
    return True


def get_favorite(favorite_id: str) -> Optional[dict]:
    for fav in load_favorites():
        if fav.get("id") == favorite_id:
            return fav
    return None
