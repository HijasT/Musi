"""Exportify import view — drag-and-drop CSV playlist import, no Spotify API setup required."""

import os
import csv
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QSizePolicy,
    QMessageBox, QScrollArea
)
from PySide6.QtCore import Qt, Signal

from gui.workers.download_queue import DownloadQueue
from gui.styles import COLORS


class DropZone(QFrame):
    """Drop zone widget for Exportify CSV files."""

    files_dropped = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dropZone")
        self.setAcceptDrops(True)
        self.setMinimumHeight(180)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(12)
        layout.setContentsMargins(40, 30, 40, 30)

        # Upload icon using text
        icon = QLabel("+")
        icon.setStyleSheet(f"""
            font-size: 48px;
            font-weight: 300;
            color: {COLORS["text_muted"]};
            background: transparent;
        """)
        icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon)

        title = QLabel("Drop your Exportify CSV file here")
        title.setObjectName("section")
        title.setStyleSheet("font-size: 16px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        hint = QLabel("or click anywhere in this box to browse")
        hint.setObjectName("muted")
        hint.setStyleSheet("font-size: 13px;")
        hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith('.csv'):
                    event.acceptProposedAction()
                    self.setObjectName("dropZoneActive")
                    self.style().unpolish(self)
                    self.style().polish(self)
                    return
        event.ignore()

    def dragLeaveEvent(self, event):
        self.setObjectName("dropZone")
        self.style().unpolish(self)
        self.style().polish(self)

    def dropEvent(self, event):
        self.setObjectName("dropZone")
        self.style().unpolish(self)
        self.style().polish(self)

        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith('.csv'):
                files.append(file_path)

        if files:
            self.files_dropped.emit(files)
            event.acceptProposedAction()
        else:
            event.ignore()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            from PySide6.QtWidgets import QFileDialog
            files, _ = QFileDialog.getOpenFileNames(
                self,
                "Select Exportify CSV Files",
                "",
                "CSV Files (*.csv)"
            )
            if files:
                self.files_dropped.emit(files)


class StepCard(QFrame):
    """A numbered step card for instructions."""

    def __init__(self, number: int, title: str, description: str, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setStyleSheet(f"StepCard {{ background-color: {COLORS['background_light']}; }}")
        self._setup_ui(number, title, description)

    def _setup_ui(self, number: int, title: str, description: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Number badge
        number_label = QLabel(str(number))
        number_label.setFixedSize(40, 40)
        number_label.setAlignment(Qt.AlignCenter)
        number_label.setStyleSheet(f"""
            background-color: {COLORS["accent"]};
            color: {COLORS["background_dark"]};
            font-size: 18px;
            font-weight: 700;
            border-radius: 20px;
        """)
        layout.addWidget(number_label)

        # Text content
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 15px; font-weight: 600;")
        text_layout.addWidget(title_label)

        desc_label = QLabel(description)
        desc_label.setObjectName("muted")
        desc_label.setStyleSheet("font-size: 13px;")
        desc_label.setWordWrap(True)
        text_layout.addWidget(desc_label)

        layout.addLayout(text_layout, 1)


class ExportifyView(QWidget):
    """Import Spotify playlists via Exportify CSV exports — no API setup required."""

    navigate_to = Signal(str)

    def __init__(self, config: dict, download_queue: DownloadQueue = None, parent=None):
        super().__init__(parent)
        self.config = config
        self.download_queue = download_queue
        self._setup_ui()

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        scroll_widget = QWidget()
        layout = QVBoxLayout(scroll_widget)
        layout.setContentsMargins(48, 40, 48, 40)
        layout.setSpacing(24)

        # Header
        title = QLabel("Exportify")
        title.setObjectName("title")
        title.setStyleSheet("font-size: 32px; font-weight: 700;")
        layout.addWidget(title)

        subtitle = QLabel("The easiest way to download your Spotify music — no API setup required")
        subtitle.setObjectName("subtitle")
        subtitle.setStyleSheet("font-size: 16px;")
        layout.addWidget(subtitle)

        # ============================================================
        # EASIEST WAY SECTION
        # ============================================================
        easiest_section = QFrame()
        easiest_section.setObjectName("cardAccent")
        easiest_layout = QVBoxLayout(easiest_section)
        easiest_layout.setContentsMargins(28, 24, 28, 28)
        easiest_layout.setSpacing(20)

        # Section header
        easiest_header = QHBoxLayout()

        easiest_title = QLabel("How Exportify Works")
        easiest_title.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {COLORS['accent']};")
        easiest_header.addWidget(easiest_title)

        easiest_header.addStretch()

        easiest_badge = QLabel("RECOMMENDED")
        easiest_badge.setStyleSheet(f"""
            background-color: {COLORS["accent"]};
            color: {COLORS["background_dark"]};
            font-size: 11px;
            font-weight: 700;
            padding: 4px 12px;
            border-radius: 4px;
        """)
        easiest_header.addWidget(easiest_badge)

        self.toggle_help_btn = QPushButton("Hide Guide")
        self.toggle_help_btn.setObjectName("ghost")
        self.toggle_help_btn.clicked.connect(self._toggle_help)
        easiest_header.addWidget(self.toggle_help_btn)

        easiest_layout.addLayout(easiest_header)

        # Collapsible help content
        self.help_container = QWidget()
        self.help_container.setStyleSheet("background: transparent;")
        help_layout = QVBoxLayout(self.help_container)
        help_layout.setContentsMargins(0, 0, 0, 0)
        help_layout.setSpacing(12)

        # Explanation
        explanation = QLabel(
            "Exportify is a free website that exports your Spotify playlists to CSV files. "
            "This is the simplest way to download your music - no Spotify API setup required!"
        )
        explanation.setStyleSheet("font-size: 14px; line-height: 1.5;")
        explanation.setWordWrap(True)
        help_layout.addWidget(explanation)

        # Steps
        steps_layout = QVBoxLayout()
        steps_layout.setSpacing(12)

        step1 = StepCard(
            1,
            "Go to exportify.net",
            "Open your web browser and visit exportify.net - it's free and safe to use"
        )
        steps_layout.addWidget(step1)

        step2 = StepCard(
            2,
            "Log in with your Spotify account",
            "Click the green button to connect your Spotify. Exportify will show all your playlists."
        )
        steps_layout.addWidget(step2)

        step3 = StepCard(
            3,
            "Export the playlist you want",
            "Click 'Export' next to any playlist. A CSV file will download to your computer."
        )
        steps_layout.addWidget(step3)

        step4 = StepCard(
            4,
            "Drag the CSV file below",
            "Drag and drop the downloaded CSV file into the box below, or click to browse."
        )
        steps_layout.addWidget(step4)

        help_layout.addLayout(steps_layout)
        easiest_layout.addWidget(self.help_container)

        # Link to exportify
        link_layout = QHBoxLayout()
        link_layout.setSpacing(12)

        exportify_btn = QPushButton("↗  Open exportify.net")
        exportify_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.12);
                color: {COLORS["text"]};
                border: 1px solid rgba(255, 255, 255, 0.2);
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.2);
                border-color: rgba(255, 255, 255, 0.35);
            }}
            QPushButton:pressed {{ background-color: rgba(255, 255, 255, 0.08); }}
        """)
        exportify_btn.setCursor(Qt.PointingHandCursor)
        exportify_btn.clicked.connect(self._open_exportify)
        link_layout.addWidget(exportify_btn)

        link_layout.addStretch()

        easiest_layout.addLayout(link_layout)

        # Drop zone
        self.drop_zone = DropZone()
        self.drop_zone.files_dropped.connect(self._handle_dropped_files)
        easiest_layout.addWidget(self.drop_zone)

        layout.addWidget(easiest_section)

        layout.addStretch()

        scroll.setWidget(scroll_widget)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def _toggle_help(self):
        visible = self.help_container.isVisible()
        self.help_container.setVisible(not visible)
        self.toggle_help_btn.setText("Show Guide" if visible else "Hide Guide")

    def _open_exportify(self):
        """Open Exportify website in browser."""
        import webbrowser
        webbrowser.open("https://exportify.net")

    def _handle_dropped_files(self, files: list):
        if not self.download_queue:
            QMessageBox.warning(self, "Error", "Download queue not available")
            return

        total_tracks = []

        for file_path in files:
            try:
                tracks = self._parse_exportify_csv(file_path)
                if tracks:
                    total_tracks.extend(tracks)
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Import Error",
                    f"Failed to parse {os.path.basename(file_path)}:\n{str(e)}"
                )

        if not total_tracks:
            QMessageBox.information(
                self,
                "No Tracks Found",
                "No valid tracks were found in the dropped files.\n\n"
                "Make sure you're using a CSV file exported from Exportify."
            )
            return

        reply = QMessageBox.question(
            self,
            "Import Tracks",
            f"Found {len(total_tracks)} tracks.\n\nAdd them to the download queue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply == QMessageBox.Yes:
            added = self._add_tracks_to_queue(total_tracks)
            QMessageBox.information(
                self,
                "Import Complete",
                f"Added {added} of {len(total_tracks)} tracks to the queue "
                f"({len(total_tracks) - added} already downloaded or skipped).\n\n"
                "Go to Downloads to start downloading."
            )
            self.navigate_to.emit("downloads")

    def _parse_exportify_csv(self, file_path: str) -> list:
        tracks = []

        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                track_name = row.get('Track Name') or row.get('track_name') or row.get('name')
                artist_name = row.get('Artist Name(s)') or row.get('artist_name') or row.get('artist')
                album_name = row.get('Album Name') or row.get('album_name') or row.get('album')
                playlist_name = row.get('Playlist Name') or row.get('playlist_name') or os.path.basename(file_path)

                if track_name and artist_name:
                    if ',' in artist_name:
                        artist_name = artist_name.split(',')[0].strip()
                    elif ';' in artist_name:
                        artist_name = artist_name.split(';')[0].strip()

                    tracks.append({
                        'track': track_name.strip(),
                        'artist': artist_name.strip(),
                        'album': album_name.strip() if album_name else '',
                        'playlist': playlist_name.replace('.csv', '').strip() if playlist_name else 'Import'
                    })

        return tracks

    def _add_tracks_to_queue(self, tracks: list) -> int:
        if not self.download_queue:
            return 0

        from gui.workers.dedupe import filter_new_tracks
        tracks = filter_new_tracks(self, self.config, tracks)

        for track_data in tracks:
            self.download_queue.add_item(
                artist=track_data['artist'],
                track=track_data['track'],
                album=track_data.get('album', ''),
                playlist=track_data.get('playlist', '')
            )

        return len(tracks)
