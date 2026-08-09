"""Musi app update checker.
Checks GitHub Releases for a newer tagged version than the running app.
"""

import json
import urllib.request
import urllib.error
from typing import Optional, Tuple

from constants import APP_VERSION, GITHUB_REPO
from utils.logger import log_info, log_warning


def get_latest_release(timeout: int = 5) -> Optional[dict]:
    """
    Fetch the latest GitHub release for this project.

    Returns a dict with 'tag_name', 'html_url', 'name', or None if the
    check fails (network unavailable, rate limited, no releases yet, etc.).
    """
    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return {
            "tag_name": data.get("tag_name", ""),
            "html_url": data.get("html_url", ""),
            "name": data.get("name", ""),
        }
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, KeyError):
        return None
    except Exception:
        return None


def parse_version(version_str: str) -> Tuple[int, ...]:
    """Parse a version string like 'v1.3.0' or '1.3.0' into a comparable tuple."""
    cleaned = (version_str or "").strip().lstrip("vV")
    parts = cleaned.split(".")
    nums = []
    for p in parts:
        digits = "".join(ch for ch in p if ch.isdigit())
        nums.append(int(digits) if digits else 0)
    while len(nums) < 3:
        nums.append(0)
    return tuple(nums)


def is_update_available(current: str, latest: str) -> bool:
    if not current or not latest:
        return False
    return parse_version(latest) > parse_version(current)


def check_app_updates() -> Optional[dict]:
    """
    Check whether a newer Musi release is available.

    Returns a dict with keys:
    - update_available: bool
    - current_version: str
    - latest_version: str
    - release_url: str
    - message: str
    Or None if unable to check (network unavailable).
    """
    release = get_latest_release()
    if not release or not release.get("tag_name"):
        return None

    latest_version = release["tag_name"]
    has_update = is_update_available(APP_VERSION, latest_version)

    return {
        "update_available": has_update,
        "current_version": APP_VERSION,
        "latest_version": latest_version,
        "release_url": release.get("html_url") or f"https://github.com/{GITHUB_REPO}/releases/latest",
        "message": (
            f"Musi update available: v{APP_VERSION} → {latest_version}"
            if has_update
            else f"Musi is up to date (v{APP_VERSION})"
        ),
    }


def notify_update_available(update_info: dict) -> None:
    """Console-friendly notification, used by the CLI entry point."""
    if not update_info:
        return

    if update_info.get("update_available"):
        message = (
            f"\n{'='*60}\n"
            f"MUSI UPDATE AVAILABLE\n"
            f"{'='*60}\n"
            f"Current version: v{update_info['current_version']}\n"
            f"Latest version:  {update_info['latest_version']}\n"
            f"\nDownload it from:\n"
            f"  {update_info['release_url']}\n"
            f"{'='*60}\n"
        )
        log_warning(message.strip())
    else:
        log_info(f"✓ {update_info.get('message', 'Musi is up to date')}")
