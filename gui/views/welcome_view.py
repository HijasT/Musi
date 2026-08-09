"""Home view: quick stats and navigation to the rest of the app."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QSizePolicy,
    QScrollArea, QGridLayout
)
from PySide6.QtCore import Qt, Signal

from gui.workers.download_queue import DownloadQueue
from gui.styles import COLORS


class StatCard(QFrame):
    """A small stat display card (e.g. '128 Music Downloaded')."""

    def __init__(self, value: str, label: str, color: str = None, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._color = color
        self._setup_ui(value, label)

    def _setup_ui(self, value: str, label: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(4)

        self.value_label = QLabel(value)
        self.value_label.setObjectName("statValue")
        if self._color:
            self.value_label.setStyleSheet(f"color: {self._color}; background: transparent; font-size: 28px;")
        layout.addWidget(self.value_label)

        caption = QLabel(label)
        caption.setObjectName("statLabel")
        layout.addWidget(caption)

    def set_value(self, value: str):
        self.value_label.setText(value)


class FeatureCard(QFrame):
    """A feature card with title, description and action button — navigates
    to another tab when clicked."""

    clicked = Signal()

    def __init__(self, title: str, description: str, button_text: str, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumWidth(200)
        self.setMinimumHeight(150)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self._setup_ui(title, description, button_text)

    def _setup_ui(self, title: str, description: str, button_text: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 18px; font-weight: 600;")
        layout.addWidget(title_label)

        # Description
        desc_label = QLabel(description)
        desc_label.setObjectName("subtitle")
        desc_label.setStyleSheet("font-size: 14px;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        layout.addStretch()

        # Button
        btn = QPushButton(button_text)
        btn.setMinimumWidth(80)
        btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        btn.clicked.connect(self.clicked.emit)
        layout.addWidget(btn)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()


class WelcomeView(QWidget):
    """Home screen: download stats and quick navigation to the rest of the app."""

    navigate_to = Signal(str)

    def __init__(self, config: dict, download_queue: DownloadQueue = None, parent=None):
        super().__init__(parent)
        self.config = config
        self.download_queue = download_queue
        self._setup_ui()
        self._refresh_stats()

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        scroll_widget = QWidget()
        layout = QVBoxLayout(scroll_widget)
        layout.setContentsMargins(48, 40, 48, 40)
        layout.setSpacing(32)

        # Header
        header = QVBoxLayout()
        header.setSpacing(12)

        title = QLabel("Welcome to Chaos Media Downloader")
        title.setObjectName("title")
        title.setStyleSheet("font-size: 32px; font-weight: 700;")
        header.addWidget(title)

        subtitle = QLabel("Download your favorite music from Spotify playlists and YouTube, or video from hundreds of other sites")
        subtitle.setObjectName("subtitle")
        subtitle.setStyleSheet("font-size: 16px;")
        header.addWidget(subtitle)

        layout.addLayout(header)

        # ============================================================
        # STATS
        # ============================================================
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)

        self.music_stat = StatCard("0", "MUSIC DOWNLOADED", COLORS["accent"])
        stats_layout.addWidget(self.music_stat)

        self.video_stat = StatCard("0", "VIDEOS DOWNLOADED", COLORS["success"])
        stats_layout.addWidget(self.video_stat)

        stats_layout.addStretch()

        layout.addLayout(stats_layout)

        # ============================================================
        # QUICK NAVIGATION
        # ============================================================
        nav_header = QLabel("Get Started")
        nav_header.setObjectName("section")
        nav_header.setStyleSheet("font-size: 18px;")
        layout.addWidget(nav_header)

        cards_grid = QGridLayout()
        cards_grid.setSpacing(16)

        exportify_card = FeatureCard(
            "Exportify",
            "The easiest way to download your Spotify music: export a playlist to CSV, no API setup required.",
            "Open Exportify"
        )
        exportify_card.clicked.connect(lambda: self.navigate_to.emit("exportify"))
        cards_grid.addWidget(exportify_card, 0, 0)

        spotify_card = FeatureCard(
            "Spotify Direct",
            "Connect to Spotify with API credentials to browse and download playlists directly from the app. Requires setup.",
            "Open Spotify"
        )
        spotify_card.clicked.connect(lambda: self.navigate_to.emit("spotify"))
        cards_grid.addWidget(spotify_card, 0, 1)

        youtube_card = FeatureCard(
            "YouTube",
            "Download music or video from YouTube (and hundreds of other sites) by pasting a link or searching.",
            "Open YouTube"
        )
        youtube_card.clicked.connect(lambda: self.navigate_to.emit("youtube"))
        cards_grid.addWidget(youtube_card, 1, 0)

        downloads_card = FeatureCard(
            "Downloads",
            "View and manage your download queue. Track progress and see completed downloads.",
            "View Queue"
        )
        downloads_card.clicked.connect(lambda: self.navigate_to.emit("downloads"))
        cards_grid.addWidget(downloads_card, 1, 1)

        settings_card = FeatureCard(
            "Settings",
            "Configure output folders, audio/video format, quality settings, and more.",
            "Open Settings"
        )
        settings_card.clicked.connect(lambda: self.navigate_to.emit("settings"))
        cards_grid.addWidget(settings_card, 2, 0)

        layout.addLayout(cards_grid)

        # Spacer
        layout.addStretch()

        # Warning card if Spotify not configured
        if not self.config.get("spotify_client_id"):
            warning_card = QFrame()
            warning_card.setObjectName("cardWarning")
            warning_layout = QHBoxLayout(warning_card)
            warning_layout.setContentsMargins(24, 20, 24, 20)
            warning_layout.setSpacing(16)

            warning_icon = QLabel("!")
            warning_icon.setFixedSize(32, 32)
            warning_icon.setAlignment(Qt.AlignCenter)
            warning_icon.setStyleSheet(f"""
                background-color: {COLORS["warning"]};
                color: {COLORS["background_dark"]};
                font-size: 18px;
                font-weight: 700;
                border-radius: 16px;
            """)
            warning_layout.addWidget(warning_icon)

            warning_text = QVBoxLayout()
            warning_text.setSpacing(4)

            warning_title = QLabel("Spotify API not configured")
            warning_title.setStyleSheet("font-weight: 600; font-size: 14px;")
            warning_text.addWidget(warning_title)

            warning_desc = QLabel(
                "To use Spotify Direct mode, set up your Spotify Client ID in Settings. "
                "Or use Exportify — it works without any setup!"
            )
            warning_desc.setObjectName("muted")
            warning_desc.setStyleSheet("font-size: 13px;")
            warning_desc.setWordWrap(True)
            warning_text.addWidget(warning_desc)

            warning_layout.addLayout(warning_text, 1)

            setup_btn = QPushButton("Set Up")
            setup_btn.setObjectName("secondary")
            setup_btn.clicked.connect(lambda: self.navigate_to.emit("settings"))
            warning_layout.addWidget(setup_btn)

            layout.addWidget(warning_card)

        scroll.setWidget(scroll_widget)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def _refresh_stats(self):
        try:
            from managers.history_manager import get_stats
            stats = get_stats()
            self.music_stat.set_value(str(stats.get("audio_count", 0)))
            self.video_stat.set_value(str(stats.get("video_count", 0)))
        except Exception:
            pass

    def showEvent(self, event):
        """Refresh stats every time Home becomes visible, so counts stay current."""
        super().showEvent(event)
        self._refresh_stats()
