"""About dialog showing version and credits."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton
)
from PySide6.QtCore import Qt


class AboutDialog(QDialog):
    """About dialog with version info and credits."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About Musi")
        self.setFixedSize(400, 300)
        self.setModal(True)

        self._setup_ui()

    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)

        # Title
        title = QLabel("Musi")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Music Downloader")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        # Version
        version = QLabel("Version 1.0.0")
        version.setAlignment(Qt.AlignCenter)
        layout.addWidget(version)

        layout.addSpacing(20)

        # Description
        description = QLabel(
            "Download music from Spotify playlists and YouTube.\n\n"
            "Uses yt-dlp for downloading and FFmpeg for audio conversion."
        )
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)
        layout.addWidget(description)

        layout.addStretch()

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
