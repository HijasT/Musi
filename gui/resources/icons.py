"""Icon management for Chaos Media Downloader GUI."""

import os
import sys
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import QSize


def _get_icons_dir() -> str:
    """Get the icons directory path (works for both script and frozen exe)."""
    if getattr(sys, 'frozen', False):
        # Running as compiled exe - PyInstaller extracts to _MEIPASS
        base_dir = sys._MEIPASS
        return os.path.join(base_dir, "gui", "resources", "icons")
    else:
        # Running as script
        return os.path.join(os.path.dirname(__file__), "icons")


# Get the icons directory path
_ICONS_DIR = _get_icons_dir()


def _get_icon_path(category: str, name: str) -> str:
    """Get the full path to an icon file."""
    return os.path.join(_ICONS_DIR, category, f"{name}.png")


def get_icon(category: str, name: str) -> QIcon:
    """
    Get a QIcon from the icons directory.

    Args:
        category: Icon category folder (app, nav, actions, titlebar)
        name: Icon name without extension

    Returns:
        QIcon object (empty if file not found)
    """
    path = _get_icon_path(category, name)
    if os.path.exists(path):
        return QIcon(path)
    return QIcon()


def get_pixmap(category: str, name: str, size: QSize = None) -> QPixmap:
    """
    Get a QPixmap from the icons directory.

    Args:
        category: Icon category folder (app, nav, actions, titlebar)
        name: Icon name without extension
        size: Optional size to scale the pixmap to

    Returns:
        QPixmap object (null if file not found)
    """
    path = _get_icon_path(category, name)
    if os.path.exists(path):
        pixmap = QPixmap(path)
        if size:
            pixmap = pixmap.scaled(size, aspectMode=1, transformMode=1)  # KeepAspectRatio, SmoothTransformation
        return pixmap
    return QPixmap()


def has_icon(category: str, name: str) -> bool:
    """Check if an icon exists."""
    return os.path.exists(_get_icon_path(category, name))


def get_app_icon() -> QIcon:
    """Get the main application icon."""
    # Try multiple naming conventions
    for name in ["app_icon", "app_ico", "icon"]:
        # Try .ico first (Windows), then .png
        ico_path = os.path.join(_ICONS_DIR, "app", f"{name}.ico")
        if os.path.exists(ico_path):
            return QIcon(ico_path)

        png_path = os.path.join(_ICONS_DIR, "app", f"{name}.png")
        if os.path.exists(png_path):
            return QIcon(png_path)

    return QIcon()


# Convenience functions for common icon categories
def nav_icon(name: str) -> QIcon:
    """Get a navigation icon."""
    return get_icon("nav", name)


def action_icon(name: str) -> QIcon:
    """Get an action icon."""
    return get_icon("actions", name)


def titlebar_icon(name: str) -> QIcon:
    """Get a titlebar icon."""
    return get_icon("titlebar", name)
