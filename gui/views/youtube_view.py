"""YouTube download view."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QGroupBox,
    QMessageBox, QTextEdit, QScrollArea, QFrame,
    QSpacerItem, QSizePolicy, QListWidget, QListWidgetItem,
    QProgressBar
)
from PySide6.QtCore import Qt

from gui.workers.download_queue import DownloadQueue
from gui.workers.video_download_worker import VideoDownloadWorker


class YouTubeView(QWidget):
    """View for downloading from YouTube URLs or search."""

    def __init__(self, config: dict, queue: DownloadQueue, parent=None):
        super().__init__(parent)
        self.config = config
        self.queue = queue
        self.video_worker = None
        self._setup_ui()
        self._refresh_favorites_list()

    def _setup_ui(self):
        """Set up the YouTube UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        scroll_widget = QWidget()
        layout = QVBoxLayout(scroll_widget)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(20)

        # Title
        title = QLabel("YouTube Download")
        title.setObjectName("title")
        layout.addWidget(title)

        subtitle = QLabel("Download music from YouTube by URL or search query")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)

        # Single URL/Search Group
        single_group = QGroupBox("Download Single Track")
        single_layout = QVBoxLayout(single_group)
        single_layout.setSpacing(12)

        url_label = QLabel("URL or search query")
        url_label.setObjectName("muted")
        single_layout.addWidget(url_label)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter YouTube URL or search query (e.g., 'Artist - Song Name')")
        self.url_input.returnPressed.connect(self._add_single_to_queue)
        single_layout.addWidget(self.url_input)

        single_btn_layout = QHBoxLayout()
        single_btn_layout.addStretch()
        add_btn = QPushButton("Add to Queue")
        add_btn.clicked.connect(self._add_single_to_queue)
        single_btn_layout.addWidget(add_btn)
        single_layout.addLayout(single_btn_layout)

        layout.addWidget(single_group)

        # Batch input group
        batch_group = QGroupBox("Batch Download")
        batch_layout = QVBoxLayout(batch_group)
        batch_layout.setSpacing(12)

        help_label = QLabel("Enter multiple search queries, one per line (format: Artist - Track Name)")
        help_label.setObjectName("muted")
        help_label.setWordWrap(True)
        batch_layout.addWidget(help_label)

        self.batch_input = QTextEdit()
        self.batch_input.setPlaceholderText(
            "Example:\n"
            "The Weeknd - Blinding Lights\n"
            "Dua Lipa - Levitating\n"
            "Ed Sheeran - Shape of You"
        )
        self.batch_input.setMinimumHeight(150)
        self.batch_input.setMaximumHeight(250)
        batch_layout.addWidget(self.batch_input)

        batch_btn_layout = QHBoxLayout()
        batch_btn_layout.addStretch()

        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("secondary")
        clear_btn.clicked.connect(self._clear_batch)
        batch_btn_layout.addWidget(clear_btn)

        add_batch_btn = QPushButton("Add All to Queue")
        add_batch_btn.clicked.connect(self._add_batch_to_queue)
        batch_btn_layout.addWidget(add_batch_btn)

        batch_layout.addLayout(batch_btn_layout)

        layout.addWidget(batch_group)

        # Video download group
        video_group = QGroupBox("Download Video")
        video_layout = QVBoxLayout(video_group)
        video_layout.setSpacing(12)

        video_help = QLabel(
            "Downloads the actual video (not just audio) from YouTube, TikTok, "
            "Instagram, Twitter/X, Reddit, Twitch, and hundreds of other yt-dlp-supported sites."
        )
        video_help.setObjectName("muted")
        video_help.setWordWrap(True)
        video_layout.addWidget(video_help)

        self.video_url_input = QLineEdit()
        self.video_url_input.setPlaceholderText("Paste a video URL")
        video_layout.addWidget(self.video_url_input)

        video_btn_layout = QHBoxLayout()
        video_btn_layout.addStretch()
        self.video_download_btn = QPushButton("Download Video")
        self.video_download_btn.clicked.connect(self._download_video)
        video_btn_layout.addWidget(self.video_download_btn)
        video_layout.addLayout(video_btn_layout)

        self.video_progress = QProgressBar()
        self.video_progress.setMinimum(0)
        self.video_progress.setMaximum(0)
        self.video_progress.setVisible(False)
        video_layout.addWidget(self.video_progress)

        layout.addWidget(video_group)

        # Favorites group
        favorites_group = QGroupBox("Favorites")
        favorites_layout = QVBoxLayout(favorites_group)
        favorites_layout.setSpacing(12)

        favorites_help = QLabel("Save links or searches here for one-click re-download later.")
        favorites_help.setObjectName("muted")
        favorites_layout.addWidget(favorites_help)

        self.favorites_list = QListWidget()
        self.favorites_list.setMaximumHeight(160)
        favorites_layout.addWidget(self.favorites_list)

        favorites_btn_layout = QHBoxLayout()
        save_fav_btn = QPushButton("Save Above URL/Query as Favorite")
        save_fav_btn.setObjectName("secondary")
        save_fav_btn.clicked.connect(self._save_url_as_favorite)
        favorites_btn_layout.addWidget(save_fav_btn)
        favorites_btn_layout.addStretch()
        remove_fav_btn = QPushButton("Remove Selected")
        remove_fav_btn.setObjectName("danger")
        remove_fav_btn.clicked.connect(self._remove_selected_favorite)
        favorites_btn_layout.addWidget(remove_fav_btn)
        download_fav_btn = QPushButton("Download Selected")
        download_fav_btn.clicked.connect(self._download_selected_favorite)
        favorites_btn_layout.addWidget(download_fav_btn)
        favorites_layout.addLayout(favorites_btn_layout)

        layout.addWidget(favorites_group)

        # Tips section
        tips_group = QGroupBox("Tips")
        tips_layout = QVBoxLayout(tips_group)
        tips_layout.setSpacing(8)

        tips_text = QLabel(
            "- For best results, use the format: Artist - Track Name\n"
            "- YouTube URLs are also supported (paste the full URL)\n"
            "- The search will find the first matching result on YouTube\n"
            "- Check the Downloads tab to monitor progress\n"
            "- Need the actual video, not just audio? Use \"Download Video\" below\n"
            "- Save frequently-used links or searches under Favorites for one-click re-download"
        )
        tips_text.setWordWrap(True)
        tips_text.setObjectName("subtitle")
        tips_layout.addWidget(tips_text)

        layout.addWidget(tips_group)

        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)

    def _parse_query(self, query: str) -> tuple:
        """
        Parse a search query into artist and track.

        Returns:
            Tuple of (artist, track)
        """
        query = query.strip()
        if not query:
            return None, None

        # Check if it's a URL
        if query.startswith(("http://", "https://", "www.")):
            return "YouTube", query

        # Try to split by common separators
        for sep in [" - ", " – ", " — ", " | "]:
            if sep in query:
                parts = query.split(sep, 1)
                return parts[0].strip(), parts[1].strip()

        # No separator found, use query as track name
        return "Unknown Artist", query

    def _add_single_to_queue(self):
        """Add single URL/search to queue."""
        query = self.url_input.text().strip()
        if not query:
            QMessageBox.warning(self, "Empty Input", "Please enter a URL or search query.")
            return

        artist, track = self._parse_query(query)
        if artist and track:
            from gui.workers.dedupe import filter_new_tracks
            if not filter_new_tracks(self, self.config, [{"artist": artist, "track": track}]):
                self.url_input.clear()
                return
            self.queue.add_track(artist, track)
            self.url_input.clear()
            QMessageBox.information(
                self,
                "Added to Queue",
                f"Added '{artist} - {track}' to download queue.\n\n"
                "Go to Downloads to start downloading."
            )
        else:
            QMessageBox.warning(self, "Invalid Input", "Could not parse the input.")

    def _add_batch_to_queue(self):
        """Add batch queries to queue."""
        text = self.batch_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Empty Input", "Please enter some search queries.")
            return

        lines = text.split("\n")
        parsed = []
        skipped = 0

        for line in lines:
            line = line.strip()
            if not line:
                continue

            artist, track = self._parse_query(line)
            if artist and track:
                parsed.append({"artist": artist, "track": track})
            else:
                skipped += 1

        from gui.workers.dedupe import filter_new_tracks
        to_add = filter_new_tracks(self, self.config, parsed)
        for t in to_add:
            self.queue.add_track(t["artist"], t["track"])
        added = len(to_add)

        if added > 0:
            self.batch_input.clear()
            message = f"Added {added} tracks to download queue."
            if skipped > 0:
                message += f"\n{skipped} lines were skipped (empty or invalid)."
            message += "\n\nGo to Downloads to start downloading."
            QMessageBox.information(self, "Added to Queue", message)
        else:
            QMessageBox.warning(self, "No Tracks Added", "No valid tracks found in the input.")

    def _clear_batch(self):
        """Clear batch input."""
        self.batch_input.clear()

    def _download_video(self):
        """Download a full video (not audio-only) via a background worker."""
        url = self.video_url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Empty Input", "Please enter a video URL.")
            return
        if not url.startswith(("http://", "https://")):
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid URL.")
            return

        reply = QMessageBox.question(
            self,
            "Download Video",
            f"Download this video?\n\n{url}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if reply != QMessageBox.Yes:
            return

        video_dir = self.config.get("video_output_dir", "videos")
        self.video_download_btn.setEnabled(False)
        self.video_progress.setVisible(True)

        self.video_worker = VideoDownloadWorker(url, video_dir, self.config)
        self.video_worker.finished.connect(self._on_video_finished)
        self.video_worker.start()

    def _on_video_finished(self, success: bool, error: str):
        self.video_progress.setVisible(False)
        self.video_download_btn.setEnabled(True)
        self.video_worker = None

        if success:
            self.video_url_input.clear()
            QMessageBox.information(self, "Download Complete", "Video downloaded successfully.")
        else:
            QMessageBox.warning(self, "Download Failed", error or "The video could not be downloaded.")

    def _refresh_favorites_list(self):
        from managers.favorites_manager import load_favorites

        self.favorites_list.clear()
        for fav in load_favorites():
            kind_label = "link" if fav.get("kind") == "link" else "search"
            item = QListWidgetItem(f"{fav['name']}  ·  {kind_label}")
            item.setData(Qt.UserRole, fav["id"])
            self.favorites_list.addItem(item)

    def _save_url_as_favorite(self):
        from managers.favorites_manager import add_favorite

        query = self.url_input.text().strip() or self.video_url_input.text().strip()
        if not query:
            QMessageBox.warning(self, "Nothing to Save", "Enter a URL or search query above first.")
            return

        artist, track = self._parse_query(query)
        is_link = query.startswith(("http://", "https://", "www."))
        default_name = query if is_link else f"{artist} - {track}"

        name = default_name[:60]
        add_favorite(name, query, "link" if is_link else "search")
        self._refresh_favorites_list()
        QMessageBox.information(self, "Saved", f"Saved \"{name}\" to favorites.")

    def _remove_selected_favorite(self):
        from managers.favorites_manager import remove_favorite

        item = self.favorites_list.currentItem()
        if not item:
            QMessageBox.information(self, "No Selection", "Select a favorite to remove.")
            return
        remove_favorite(item.data(Qt.UserRole))
        self._refresh_favorites_list()

    def _download_selected_favorite(self):
        from managers.favorites_manager import get_favorite

        item = self.favorites_list.currentItem()
        if not item:
            QMessageBox.information(self, "No Selection", "Select a favorite to download.")
            return

        fav = get_favorite(item.data(Qt.UserRole))
        if not fav:
            return

        # Both link and search favorites go through the same audio queue path —
        # _parse_query() already handles distinguishing a URL from a search string.
        self.url_input.setText(fav["value"])
        self._add_single_to_queue()
