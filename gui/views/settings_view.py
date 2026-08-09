"""Settings view for configuration management."""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QComboBox, QCheckBox,
    QGroupBox, QFormLayout, QFileDialog, QMessageBox,
    QSpacerItem, QSizePolicy, QScrollArea, QFrame,
    QProgressBar
)
from PySide6.QtCore import Signal

from config import save_config, validate_config, DEFAULT_CONFIG, load_config
from constants import AUDIO_BITRATE_OPTIONS, VALID_AUDIO_EXTENSIONS, VIDEO_FORMAT_OPTIONS, APP_VERSION, GITHUB_REPO
from gui.styles import COLORS
from utils.ffmpeg import check_ffmpeg_available
from tools.ytdlp_update_checker import check_ytdlp_updates


class SettingsView(QWidget):
    """Settings configuration view."""

    config_saved = Signal()  # Emits when config is saved

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config
        self.ffmpeg_worker = None
        self.ytdlp_worker = None
        self.cleanup_worker = None
        self.convert_worker = None
        self.app_update_worker = None
        self._setup_ui()
        self._load_values()
        self._check_ffmpeg_status()
        self._check_ytdlp_status()

    def _setup_ui(self):
        """Set up the settings UI."""
        # Main layout with scroll area
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        scroll_widget = QWidget()
        layout = QVBoxLayout(scroll_widget)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(16)

        # Title
        title = QLabel("Settings")
        title.setObjectName("title")
        layout.addWidget(title)

        # Dependencies Group
        deps_group = QGroupBox("Dependencies")
        deps_layout = QVBoxLayout(deps_group)
        deps_layout.setSpacing(14)

        # --- FFmpeg section ---
        ffmpeg_header = QLabel("FFmpeg")
        ffmpeg_header.setObjectName("section")
        deps_layout.addWidget(ffmpeg_header)

        ffmpeg_desc = QLabel("Required for audio conversion.")
        ffmpeg_desc.setObjectName("muted")
        deps_layout.addWidget(ffmpeg_desc)

        status_row = QHBoxLayout()
        self.ffmpeg_status_icon = QLabel("●")
        self.ffmpeg_status_icon.setFixedWidth(20)
        status_row.addWidget(self.ffmpeg_status_icon)
        self.ffmpeg_status_label = QLabel("Checking...")
        self.ffmpeg_status_label.setWordWrap(True)
        status_row.addWidget(self.ffmpeg_status_label, 1)
        self.ffmpeg_install_btn = QPushButton("Install FFmpeg")
        self.ffmpeg_install_btn.setObjectName("secondary")
        self.ffmpeg_install_btn.clicked.connect(self._install_ffmpeg)
        status_row.addWidget(self.ffmpeg_install_btn)
        self.ffmpeg_refresh_btn = QPushButton("Refresh")
        self.ffmpeg_refresh_btn.setObjectName("secondary")
        self.ffmpeg_refresh_btn.setFixedWidth(70)
        self.ffmpeg_refresh_btn.clicked.connect(self._check_ffmpeg_status)
        status_row.addWidget(self.ffmpeg_refresh_btn)
        deps_layout.addLayout(status_row)

        self.ffmpeg_progress = QProgressBar()
        self.ffmpeg_progress.setVisible(False)
        deps_layout.addWidget(self.ffmpeg_progress)
        self.ffmpeg_progress_label = QLabel("")
        self.ffmpeg_progress_label.setObjectName("subtitle")
        self.ffmpeg_progress_label.setVisible(False)
        deps_layout.addWidget(self.ffmpeg_progress_label)

        # FFmpeg custom path
        ffmpeg_path_label = QLabel("Custom path")
        ffmpeg_path_label.setObjectName("muted")
        deps_layout.addWidget(ffmpeg_path_label)
        ffmpeg_path_row = QHBoxLayout()
        self.ffmpeg_path_input = QLineEdit()
        self.ffmpeg_path_input.setPlaceholderText("Auto-detect (leave empty)")
        ffmpeg_path_row.addWidget(self.ffmpeg_path_input, 1)
        ffmpeg_browse_btn = QPushButton("Browse")
        ffmpeg_browse_btn.setObjectName("secondary")
        ffmpeg_browse_btn.setFixedWidth(70)
        ffmpeg_browse_btn.clicked.connect(self._browse_ffmpeg_path)
        ffmpeg_path_row.addWidget(ffmpeg_browse_btn)
        deps_layout.addLayout(ffmpeg_path_row)

        # --- Separator ---
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {COLORS['border']};")
        sep.setFixedHeight(1)
        deps_layout.addWidget(sep)

        # --- yt-dlp section ---
        ytdlp_header = QLabel("yt-dlp")
        ytdlp_header.setObjectName("section")
        deps_layout.addWidget(ytdlp_header)

        ytdlp_desc = QLabel("Required for downloading from YouTube and other sources.")
        ytdlp_desc.setObjectName("muted")
        deps_layout.addWidget(ytdlp_desc)

        ytdlp_status_row = QHBoxLayout()
        self.ytdlp_status_icon = QLabel("●")
        self.ytdlp_status_icon.setFixedWidth(20)
        ytdlp_status_row.addWidget(self.ytdlp_status_icon)
        self.ytdlp_status_label = QLabel("Checking...")
        self.ytdlp_status_label.setWordWrap(True)
        ytdlp_status_row.addWidget(self.ytdlp_status_label, 1)
        self.ytdlp_update_btn = QPushButton("Check for Updates")
        self.ytdlp_update_btn.setObjectName("secondary")
        self.ytdlp_update_btn.clicked.connect(self._check_ytdlp_updates)
        ytdlp_status_row.addWidget(self.ytdlp_update_btn)
        self.ytdlp_refresh_btn = QPushButton("Refresh")
        self.ytdlp_refresh_btn.setObjectName("secondary")
        self.ytdlp_refresh_btn.setFixedWidth(70)
        self.ytdlp_refresh_btn.clicked.connect(self._check_ytdlp_status)
        ytdlp_status_row.addWidget(self.ytdlp_refresh_btn)
        deps_layout.addLayout(ytdlp_status_row)

        self.ytdlp_progress = QProgressBar()
        self.ytdlp_progress.setVisible(False)
        deps_layout.addWidget(self.ytdlp_progress)
        self.ytdlp_progress_label = QLabel("")
        self.ytdlp_progress_label.setObjectName("subtitle")
        self.ytdlp_progress_label.setVisible(False)
        deps_layout.addWidget(self.ytdlp_progress_label)

        # yt-dlp custom path
        ytdlp_path_label = QLabel("Custom path")
        ytdlp_path_label.setObjectName("muted")
        deps_layout.addWidget(ytdlp_path_label)
        ytdlp_path_row = QHBoxLayout()
        self.ytdlp_path_input = QLineEdit()
        self.ytdlp_path_input.setPlaceholderText("Auto-detect (leave empty)")
        ytdlp_path_row.addWidget(self.ytdlp_path_input, 1)
        ytdlp_browse_btn = QPushButton("Browse")
        ytdlp_browse_btn.setObjectName("secondary")
        ytdlp_browse_btn.setFixedWidth(70)
        ytdlp_browse_btn.clicked.connect(self._browse_ytdlp_path)
        ytdlp_path_row.addWidget(ytdlp_browse_btn)
        deps_layout.addLayout(ytdlp_path_row)

        layout.addWidget(deps_group)

        # About & Updates Group
        about_group = QGroupBox("About && Updates")
        about_layout = QVBoxLayout(about_group)
        about_layout.setSpacing(10)

        version_row = QHBoxLayout()
        version_label = QLabel(f"Chaos Media Downloader v{APP_VERSION}")
        version_row.addWidget(version_label, 1)
        self.check_updates_btn = QPushButton("Check for Updates")
        self.check_updates_btn.setObjectName("secondary")
        self.check_updates_btn.clicked.connect(self._check_app_updates)
        version_row.addWidget(self.check_updates_btn)
        about_layout.addLayout(version_row)

        self.update_status_label = QLabel("")
        self.update_status_label.setObjectName("muted")
        self.update_status_label.setWordWrap(True)
        about_layout.addWidget(self.update_status_label)

        github_btn = QPushButton("Open GitHub Repository")
        github_btn.setObjectName("secondary")
        github_btn.clicked.connect(self._open_github)
        about_layout.addWidget(github_btn)

        layout.addWidget(about_group)

        # Output Settings Group
        output_group = QGroupBox("Output Settings")
        output_layout = QVBoxLayout(output_group)
        output_layout.setSpacing(10)

        output_dir_label = QLabel("Output directory")
        output_dir_label.setObjectName("muted")
        output_layout.addWidget(output_dir_label)
        output_dir_row = QHBoxLayout()
        self.output_dir_input = QLineEdit()
        self.output_dir_input.setPlaceholderText("Select output directory...")
        output_dir_row.addWidget(self.output_dir_input, 1)
        browse_btn = QPushButton("Browse")
        browse_btn.setObjectName("secondary")
        browse_btn.setFixedWidth(70)
        browse_btn.clicked.connect(self._browse_output_dir)
        output_dir_row.addWidget(browse_btn)
        output_layout.addLayout(output_dir_row)

        format_label = QLabel("Audio format")
        format_label.setObjectName("muted")
        output_layout.addWidget(format_label)
        self.format_combo = QComboBox()
        self.format_combo.addItems(["mp3", "flac", "wav", "aac", "ogg", "m4a"])
        output_layout.addWidget(self.format_combo)

        bitrate_label = QLabel("Audio bitrate")
        bitrate_label.setObjectName("muted")
        output_layout.addWidget(bitrate_label)
        self.bitrate_combo = QComboBox()
        for bitrate, desc in AUDIO_BITRATE_OPTIONS.items():
            self.bitrate_combo.addItem(f"{bitrate} - {desc}", userData=bitrate)
        output_layout.addWidget(self.bitrate_combo)

        # --- Separator ---
        video_sep = QFrame()
        video_sep.setFrameShape(QFrame.HLine)
        video_sep.setStyleSheet(f"color: {COLORS['border']};")
        video_sep.setFixedHeight(1)
        output_layout.addWidget(video_sep)

        video_dir_label = QLabel("Video output directory")
        video_dir_label.setObjectName("muted")
        output_layout.addWidget(video_dir_label)
        video_dir_row = QHBoxLayout()
        self.video_output_dir_input = QLineEdit()
        self.video_output_dir_input.setPlaceholderText("Select video output directory...")
        video_dir_row.addWidget(self.video_output_dir_input, 1)
        video_browse_btn = QPushButton("Browse")
        video_browse_btn.setObjectName("secondary")
        video_browse_btn.setFixedWidth(70)
        video_browse_btn.clicked.connect(self._browse_video_output_dir)
        video_dir_row.addWidget(video_browse_btn)
        output_layout.addLayout(video_dir_row)

        video_format_label = QLabel("Video format")
        video_format_label.setObjectName("muted")
        output_layout.addWidget(video_format_label)
        self.video_format_combo = QComboBox()
        for fmt, desc in VIDEO_FORMAT_OPTIONS.items():
            self.video_format_combo.addItem(f"{fmt} - {desc}", userData=fmt)
        output_layout.addWidget(self.video_format_combo)

        self.embed_video_subs_check = QCheckBox("Embed subtitles in downloaded videos")
        output_layout.addWidget(self.embed_video_subs_check)

        layout.addWidget(output_group)

        # Spotify Settings Group
        spotify_group = QGroupBox("Spotify Settings")
        spotify_layout = QVBoxLayout(spotify_group)
        spotify_layout.setSpacing(10)

        client_id_label = QLabel("Client ID")
        client_id_label.setObjectName("muted")
        spotify_layout.addWidget(client_id_label)
        self.client_id_input = QLineEdit()
        self.client_id_input.setPlaceholderText("Enter your Spotify Client ID")
        spotify_layout.addWidget(self.client_id_input)

        redirect_label = QLabel("Redirect URI")
        redirect_label.setObjectName("muted")
        spotify_layout.addWidget(redirect_label)
        self.redirect_uri_input = QLineEdit()
        self.redirect_uri_input.setReadOnly(True)
        spotify_layout.addWidget(self.redirect_uri_input)

        help_label = QLabel(
            "To get a Spotify Client ID:\n"
            "1. Go to developer.spotify.com/dashboard\n"
            "2. Create a new app\n"
            "3. Add http://127.0.0.1:8888/callback to Redirect URIs\n"
            "4. Copy the Client ID here"
        )
        help_label.setObjectName("subtitle")
        help_label.setWordWrap(True)
        spotify_layout.addWidget(help_label)

        layout.addWidget(spotify_group)

        # Download Settings Group
        download_group = QGroupBox("Download Settings")
        download_layout = QVBoxLayout(download_group)
        download_layout.setSpacing(10)

        sleep_label = QLabel("Sleep between downloads (seconds)")
        sleep_label.setObjectName("muted")
        download_layout.addWidget(sleep_label)
        self.sleep_input = QLineEdit()
        self.sleep_input.setPlaceholderText("5")
        self.sleep_input.setMaximumWidth(200)
        download_layout.addWidget(self.sleep_input)

        retry_label = QLabel("Retry attempts")
        retry_label.setObjectName("muted")
        download_layout.addWidget(retry_label)
        self.retry_input = QLineEdit()
        self.retry_input.setPlaceholderText("3")
        self.retry_input.setMaximumWidth(200)
        download_layout.addWidget(self.retry_input)

        ytdlp_args_label = QLabel("Extra yt-dlp arguments")
        ytdlp_args_label.setObjectName("muted")
        download_layout.addWidget(ytdlp_args_label)
        self.ytdlp_args_input = QLineEdit()
        self.ytdlp_args_input.setPlaceholderText('e.g. --cookies cookies.txt --limit-rate 1M')
        download_layout.addWidget(self.ytdlp_args_input)

        ffmpeg_args_label = QLabel("Extra ffmpeg arguments")
        ffmpeg_args_label.setObjectName("muted")
        download_layout.addWidget(ffmpeg_args_label)
        self.ffmpeg_args_input = QLineEdit()
        self.ffmpeg_args_input.setPlaceholderText('e.g. -ar 44100')
        download_layout.addWidget(self.ffmpeg_args_input)

        layout.addWidget(download_group)

        # Metadata Settings Group
        metadata_group = QGroupBox("Metadata Settings")
        metadata_layout = QVBoxLayout(metadata_group)
        metadata_layout.setSpacing(10)

        self.metadata_check = QCheckBox("Enable metadata embedding")
        metadata_layout.addWidget(self.metadata_check)

        template_label = QLabel("Template")
        template_label.setObjectName("muted")
        metadata_layout.addWidget(template_label)
        self.template_combo = QComboBox()
        self.template_combo.addItems(["basic", "comprehensive", "dj-mix"])
        metadata_layout.addWidget(self.template_combo)

        self.musicbrainz_check = QCheckBox("Enable MusicBrainz lookup")
        metadata_layout.addWidget(self.musicbrainz_check)

        self.lyrics_check = QCheckBox("Auto-fetch lyrics (via lrclib.net)")
        metadata_layout.addWidget(self.lyrics_check)

        layout.addWidget(metadata_group)

        # Backup Settings Group
        backup_group = QGroupBox("Backup Settings")
        backup_layout = QVBoxLayout(backup_group)
        backup_layout.setSpacing(10)

        self.backup_check = QCheckBox("Enable automatic backups")
        backup_layout.addWidget(self.backup_check)

        max_backups_label = QLabel("Max backups")
        max_backups_label.setObjectName("muted")
        backup_layout.addWidget(max_backups_label)
        self.max_backups_input = QLineEdit()
        self.max_backups_input.setPlaceholderText("10")
        self.max_backups_input.setMaximumWidth(200)
        backup_layout.addWidget(self.max_backups_input)

        layout.addWidget(backup_group)

        # Library Maintenance Group
        cleanup_group = QGroupBox("Library Maintenance")
        cleanup_layout = QVBoxLayout(cleanup_group)
        cleanup_layout.setSpacing(10)

        cleanup_desc = QLabel(
            "Scan your music library for empty or corrupted files and remove them."
        )
        cleanup_desc.setObjectName("muted")
        cleanup_desc.setWordWrap(True)
        cleanup_layout.addWidget(cleanup_desc)

        self.auto_redownload_check = QCheckBox("Auto-redownload corrupted files after removal")
        cleanup_layout.addWidget(self.auto_redownload_check)

        cleanup_status_row = QHBoxLayout()
        self.cleanup_status_label = QLabel("")
        self.cleanup_status_label.setObjectName("muted")
        cleanup_status_row.addWidget(self.cleanup_status_label, 1)
        self.cleanup_run_btn = QPushButton("Clean Library")
        self.cleanup_run_btn.setObjectName("secondary")
        self.cleanup_run_btn.clicked.connect(self._run_library_cleanup)
        cleanup_status_row.addWidget(self.cleanup_run_btn)
        cleanup_layout.addLayout(cleanup_status_row)

        self.cleanup_progress = QProgressBar()
        self.cleanup_progress.setMinimum(0)
        self.cleanup_progress.setMaximum(0)  # indeterminate — no per-file progress signal
        self.cleanup_progress.setVisible(False)
        cleanup_layout.addWidget(self.cleanup_progress)

        # --- Separator ---
        convert_sep = QFrame()
        convert_sep.setFrameShape(QFrame.HLine)
        convert_sep.setStyleSheet(f"color: {COLORS['border']};")
        convert_sep.setFixedHeight(1)
        cleanup_layout.addWidget(convert_sep)

        convert_desc = QLabel(
            "Convert your entire library to a different format/bitrate using ffmpeg. "
            "Originals are kept unless you choose to delete them."
        )
        convert_desc.setObjectName("muted")
        convert_desc.setWordWrap(True)
        cleanup_layout.addWidget(convert_desc)

        convert_options_row = QHBoxLayout()
        self.convert_format_combo = QComboBox()
        self.convert_format_combo.addItems(sorted(ext.strip(".") for ext in VALID_AUDIO_EXTENSIONS))
        convert_options_row.addWidget(self.convert_format_combo)

        self.convert_bitrate_combo = QComboBox()
        for bitrate, desc in AUDIO_BITRATE_OPTIONS.items():
            self.convert_bitrate_combo.addItem(f"{bitrate} - {desc}", userData=bitrate)
        convert_options_row.addWidget(self.convert_bitrate_combo)
        cleanup_layout.addLayout(convert_options_row)

        self.convert_delete_originals_check = QCheckBox("Delete original files after conversion")
        cleanup_layout.addWidget(self.convert_delete_originals_check)

        convert_status_row = QHBoxLayout()
        self.convert_status_label = QLabel("")
        self.convert_status_label.setObjectName("muted")
        convert_status_row.addWidget(self.convert_status_label, 1)
        self.convert_run_btn = QPushButton("Convert Library")
        self.convert_run_btn.setObjectName("secondary")
        self.convert_run_btn.clicked.connect(self._run_convert_audio)
        convert_status_row.addWidget(self.convert_run_btn)
        cleanup_layout.addLayout(convert_status_row)

        self.convert_progress = QProgressBar()
        self.convert_progress.setMinimum(0)
        self.convert_progress.setMaximum(0)
        self.convert_progress.setVisible(False)
        cleanup_layout.addWidget(self.convert_progress)

        layout.addWidget(cleanup_group)

        # Spacer
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.setObjectName("secondary")
        reset_btn.clicked.connect(self._reset_to_defaults)
        buttons_layout.addWidget(reset_btn)

        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self._save_settings)
        buttons_layout.addWidget(save_btn)

        layout.addLayout(buttons_layout)

        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)

    def _load_values(self):
        """Load current config values into the form."""
        self.output_dir_input.setText(self.config.get("output_dir", "music"))
        self.format_combo.setCurrentText(self.config.get("audio_format", "mp3"))
        bitrate_index = self.bitrate_combo.findData(self.config.get("audio_bitrate", "320k"))
        self.bitrate_combo.setCurrentIndex(bitrate_index if bitrate_index >= 0 else self.bitrate_combo.count() - 1)
        self.video_output_dir_input.setText(self.config.get("video_output_dir", "videos"))
        video_format_index = self.video_format_combo.findData(self.config.get("video_format", "mp4"))
        self.video_format_combo.setCurrentIndex(video_format_index if video_format_index >= 0 else 0)
        self.embed_video_subs_check.setChecked(self.config.get("embed_video_subs", True))
        self.client_id_input.setText(self.config.get("spotify_client_id", ""))
        self.redirect_uri_input.setText(self.config.get("spotify_redirect_uri", "http://127.0.0.1:8888/callback"))
        self.sleep_input.setText(str(self.config.get("sleep_between", 5)))
        self.retry_input.setText(str(self.config.get("retry_attempts", 3)))
        self.ytdlp_args_input.setText(self.config.get("ytdlp_extra_args", ""))
        self.ffmpeg_args_input.setText(self.config.get("ffmpeg_extra_args", ""))
        self.metadata_check.setChecked(self.config.get("enable_metadata_embedding", True))
        self.template_combo.setCurrentText(self.config.get("metadata_template", "basic"))
        self.musicbrainz_check.setChecked(self.config.get("enable_musicbrainz_lookup", True))
        self.lyrics_check.setChecked(self.config.get("enable_lyrics_fetch", True))
        self.backup_check.setChecked(self.config.get("auto_backup", True))
        self.max_backups_input.setText(str(self.config.get("max_backups", 10)))
        self.auto_redownload_check.setChecked(self.config.get("auto_redownload_corrupted", True))
        self.ffmpeg_path_input.setText(self.config.get("ffmpeg_path", ""))
        self.ytdlp_path_input.setText(self.config.get("ytdlp_path", ""))

    def _check_ffmpeg_status(self):
        """Check FFmpeg installation status."""
        available, message = check_ffmpeg_available()

        if available:
            self.ffmpeg_status_icon.setStyleSheet(f"color: {COLORS['success']}; font-size: 14px;")
            self.ffmpeg_status_label.setText(f"Installed: {message.replace('FFmpeg found at: ', '')}")
            self.ffmpeg_status_label.setStyleSheet(f"color: {COLORS['success']};")
            self.ffmpeg_install_btn.setText("Reinstall")
        else:
            self.ffmpeg_status_icon.setStyleSheet(f"color: {COLORS['error']}; font-size: 14px;")
            self.ffmpeg_status_label.setText("Not installed")
            self.ffmpeg_status_label.setStyleSheet(f"color: {COLORS['error']};")
            self.ffmpeg_install_btn.setText("Install FFmpeg")

    def _install_ffmpeg(self):
        """Start FFmpeg installation."""
        from gui.workers.ffmpeg_installer import FFmpegInstallerWorker

        # Confirm installation
        reply = QMessageBox.question(
            self,
            "Install FFmpeg",
            "This will download and install FFmpeg (~100MB).\n\n"
            "The installation is required for audio conversion.\n\n"
            "Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply != QMessageBox.Yes:
            return

        # Disable buttons during installation
        self.ffmpeg_install_btn.setEnabled(False)
        self.ffmpeg_refresh_btn.setEnabled(False)

        # Show progress
        self.ffmpeg_progress.setVisible(True)
        self.ffmpeg_progress_label.setVisible(True)
        self.ffmpeg_progress.setValue(0)

        # Create and start worker
        self.ffmpeg_worker = FFmpegInstallerWorker()
        self.ffmpeg_worker.progress.connect(self._on_ffmpeg_progress)
        self.ffmpeg_worker.finished.connect(self._on_ffmpeg_finished)
        self.ffmpeg_worker.start()

    def _on_ffmpeg_progress(self, percent: int, message: str):
        """Handle FFmpeg installation progress."""
        self.ffmpeg_progress.setValue(percent)
        self.ffmpeg_progress_label.setText(message)

    def _on_ffmpeg_finished(self, success: bool, message: str):
        """Handle FFmpeg installation completion."""
        # Hide progress
        self.ffmpeg_progress.setVisible(False)
        self.ffmpeg_progress_label.setVisible(False)

        # Re-enable buttons
        self.ffmpeg_install_btn.setEnabled(True)
        self.ffmpeg_refresh_btn.setEnabled(True)

        # Show result
        if success:
            QMessageBox.information(self, "Installation Complete", message)
            self._check_ffmpeg_status()
        else:
            QMessageBox.warning(self, "Installation Failed", message)
            self._check_ffmpeg_status()

        # Clean up worker
        self.ffmpeg_worker = None

    def _check_ytdlp_status(self):
        """Check yt-dlp installation and version status."""
        import shutil
        import subprocess

        version = None
        found_path = None

        # Check custom path from config first
        custom_path = self.config.get("ytdlp_path", "")
        if custom_path and os.path.isfile(custom_path):
            found_path = custom_path
            try:
                result = subprocess.run(
                    [custom_path, "--version"],
                    capture_output=True, text=True, timeout=3
                )
                if result.returncode == 0:
                    version = result.stdout.strip()
            except Exception:
                pass
        else:
            # Check PATH
            ytdlp_bin = shutil.which("yt-dlp")
            if ytdlp_bin:
                found_path = ytdlp_bin
                try:
                    result = subprocess.run(
                        [ytdlp_bin, "--version"],
                        capture_output=True, text=True, timeout=3
                    )
                    if result.returncode == 0:
                        version = result.stdout.strip()
                except Exception:
                    pass

        if found_path and version:
            self.ytdlp_status_icon.setStyleSheet(f"color: {COLORS['success']}; font-size: 14px;")
            self.ytdlp_status_label.setText(f"Installed: {version} ({found_path})")
            self.ytdlp_status_label.setStyleSheet(f"color: {COLORS['success']};")
            self.ytdlp_update_btn.setText("Check for Updates")
            self.ytdlp_update_btn.setEnabled(True)
        elif found_path:
            self.ytdlp_status_icon.setStyleSheet(f"color: {COLORS['success']}; font-size: 14px;")
            self.ytdlp_status_label.setText(f"Installed: {found_path}")
            self.ytdlp_status_label.setStyleSheet(f"color: {COLORS['success']};")
            self.ytdlp_update_btn.setText("Check for Updates")
            self.ytdlp_update_btn.setEnabled(True)
        else:
            self.ytdlp_status_icon.setStyleSheet(f"color: {COLORS['error']}; font-size: 14px;")
            self.ytdlp_status_label.setText("Not installed")
            self.ytdlp_status_label.setStyleSheet(f"color: {COLORS['error']};")
            self.ytdlp_update_btn.setText("Install yt-dlp")
            self.ytdlp_update_btn.setEnabled(True)

    def _check_ytdlp_updates(self):
        """Start yt-dlp update check and installation."""
        import shutil

        # Fast local check only — no network call
        ytdlp_bin = self.config.get("ytdlp_path", "") or shutil.which("yt-dlp")
        use_standalone = not (ytdlp_bin and os.path.isfile(ytdlp_bin))

        if use_standalone:
            message = (
                "yt-dlp is not installed. Install it now?\n\n"
                "This will download the standalone yt-dlp binary.\n\n"
                "Continue?"
            )
        else:
            message = (
                "Download and install the latest yt-dlp?\n\n"
                "Continue?"
            )

        reply = QMessageBox.question(
            self,
            "Update yt-dlp",
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply != QMessageBox.Yes:
            return

        self.ytdlp_update_btn.setEnabled(False)
        self.ytdlp_refresh_btn.setEnabled(False)

        self.ytdlp_progress.setVisible(True)
        self.ytdlp_progress_label.setVisible(True)
        self.ytdlp_progress.setValue(0)

        if use_standalone:
            from gui.workers.ytdlp_installer import YtdlpInstallerWorker
            self.ytdlp_worker = YtdlpInstallerWorker()
        else:
            from gui.workers.ytdlp_updater import YtdlpUpdaterWorker
            self.ytdlp_worker = YtdlpUpdaterWorker()

        self.ytdlp_worker.progress.connect(self._on_ytdlp_progress)
        self.ytdlp_worker.finished.connect(self._on_ytdlp_finished)
        self.ytdlp_worker.start()

    def _on_ytdlp_progress(self, percent: int, message: str):
        """Handle yt-dlp update progress."""
        self.ytdlp_progress.setValue(percent)
        self.ytdlp_progress_label.setText(message)

    def _on_ytdlp_finished(self, success: bool, message: str):
        """Handle yt-dlp update completion."""
        self.ytdlp_progress.setVisible(False)
        self.ytdlp_progress_label.setVisible(False)
        self.ytdlp_update_btn.setEnabled(True)
        self.ytdlp_refresh_btn.setEnabled(True)

        if success:
            # Ensure newly installed binary's dir is on PATH
            if hasattr(self.ytdlp_worker, 'install_dir'):
                install_dir = self.ytdlp_worker.install_dir
                if install_dir not in os.environ.get('PATH', ''):
                    os.environ['PATH'] = install_dir + os.pathsep + os.environ.get('PATH', '')
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.warning(self, "Install Failed", message)

        self.ytdlp_worker = None
        self._check_ytdlp_status()

    def _run_library_cleanup(self):
        """Scan the music library and remove/redownload broken files."""
        redownload = self.auto_redownload_check.isChecked()
        message = (
            "This will scan your music library for empty or corrupted files and remove them."
        )
        if redownload:
            message += "\n\nCorrupted files will be automatically redownloaded."
        message += "\n\nThis may take a while for large libraries. Continue?"

        reply = QMessageBox.question(
            self,
            "Clean Library",
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        if reply != QMessageBox.Yes:
            return

        # Run against current in-memory settings, including any unsaved checkbox state
        run_config = dict(self.config)
        run_config["auto_redownload_corrupted"] = redownload

        self.cleanup_run_btn.setEnabled(False)
        self.cleanup_status_label.setText("Scanning library...")
        self.cleanup_progress.setVisible(True)

        from gui.workers.library_cleanup_worker import LibraryCleanupWorker
        self.cleanup_worker = LibraryCleanupWorker(run_config)
        self.cleanup_worker.finished.connect(self._on_cleanup_finished)
        self.cleanup_worker.start()

    def _on_cleanup_finished(self, result: dict):
        """Handle library cleanup completion."""
        self.cleanup_progress.setVisible(False)
        self.cleanup_run_btn.setEnabled(True)
        self.cleanup_worker = None

        if result.get("error"):
            self.cleanup_status_label.setText("Failed")
            QMessageBox.warning(self, "Library Cleanup Failed", result["error"])
            return

        removed = result.get("removed", 0)
        redownloaded = result.get("redownloaded", 0)
        skipped = result.get("skipped", 0)

        if removed == 0:
            self.cleanup_status_label.setText("No broken files found")
            QMessageBox.information(self, "Library Clean", "No broken files were found.")
            return

        self.cleanup_status_label.setText(f"Removed {removed}, redownloaded {redownloaded}")

        summary = f"Removed {removed} broken file(s)."
        if self.auto_redownload_check.isChecked():
            summary += f"\nRedownloaded {redownloaded}."
            if skipped:
                summary += f"\nSkipped {skipped} (filename didn't match \"Artist - Title\")."
        QMessageBox.information(self, "Library Cleanup Complete", summary)

    def _run_convert_audio(self):
        """Convert the music library to the selected format/bitrate via ffmpeg."""
        target_format = self.convert_format_combo.currentText()
        target_bitrate = self.convert_bitrate_combo.currentData()
        delete_originals = self.convert_delete_originals_check.isChecked()

        message = f"This will convert your library to {target_format.upper()} at {target_bitrate}."
        if delete_originals:
            message += "\n\nOriginal files will be DELETED after a successful conversion."
        else:
            message += "\n\nOriginal files will be kept alongside the converted copies."
        message += "\n\nThis may take a while for large libraries. Continue?"

        reply = QMessageBox.question(
            self,
            "Convert Library",
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        if reply != QMessageBox.Yes:
            return

        self.convert_run_btn.setEnabled(False)
        self.convert_status_label.setText(f"Converting to {target_format}...")
        self.convert_progress.setVisible(True)

        from gui.workers.convert_audio_worker import ConvertAudioWorker
        self.convert_worker = ConvertAudioWorker(
            dict(self.config), target_format, target_bitrate, delete_originals=delete_originals,
        )
        self.convert_worker.finished.connect(self._on_convert_finished)
        self.convert_worker.start()

    def _on_convert_finished(self, result: dict):
        """Handle audio conversion completion."""
        self.convert_progress.setVisible(False)
        self.convert_run_btn.setEnabled(True)
        self.convert_worker = None

        if result.get("error"):
            self.convert_status_label.setText("Failed")
            QMessageBox.warning(self, "Conversion Failed", result["error"])
            return

        converted = result.get("converted", 0)
        skipped = result.get("skipped", 0)
        failed = result.get("failed", 0)

        self.convert_status_label.setText(f"Converted {converted}, skipped {skipped}, failed {failed}")

        if converted == 0 and skipped == 0 and failed == 0:
            QMessageBox.information(self, "Convert Library", "No matching files found to convert.")
            return

        summary = f"Converted {converted} file(s)."
        if skipped:
            summary += f"\nSkipped {skipped} (already in target format or naming conflict)."
        if failed:
            summary += f"\nFailed {failed}."
        QMessageBox.information(self, "Conversion Complete", summary)

    def _browse_ffmpeg_path(self):
        """Open file browser for FFmpeg binary."""
        path, _ = QFileDialog.getOpenFileName(self, "Select FFmpeg Binary")
        if path:
            self.ffmpeg_path_input.setText(path)

    def _browse_ytdlp_path(self):
        """Open file browser for yt-dlp binary."""
        path, _ = QFileDialog.getOpenFileName(self, "Select yt-dlp Binary")
        if path:
            self.ytdlp_path_input.setText(path)

    def _browse_output_dir(self):
        """Open folder browser for output directory."""
        current_dir = self.output_dir_input.text() or os.path.expanduser("~")

        # Make sure the current dir exists, otherwise use home
        if not os.path.isdir(current_dir):
            current_dir = os.path.expanduser("~")

        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            current_dir,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        if folder:
            # Use the selected folder path
            self.output_dir_input.setText(folder)
            # Auto-save to make sure it takes effect
            self._update_config_value("output_dir", folder)

    def _browse_video_output_dir(self):
        """Open folder browser for video output directory."""
        current_dir = self.video_output_dir_input.text() or os.path.expanduser("~")

        if not os.path.isdir(current_dir):
            current_dir = os.path.expanduser("~")

        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Video Output Directory",
            current_dir,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        if folder:
            self.video_output_dir_input.setText(folder)
            self._update_config_value("video_output_dir", folder)

    def _check_app_updates(self):
        """Manually check GitHub for a newer release (shows result either way,
        unlike the silent startup check)."""
        self.check_updates_btn.setEnabled(False)
        self.update_status_label.setText("Checking...")

        from gui.workers.app_update_worker import AppUpdateCheckWorker
        self.app_update_worker = AppUpdateCheckWorker()
        self.app_update_worker.finished.connect(self._on_app_update_check_finished)
        self.app_update_worker.start()

    def _on_app_update_check_finished(self, update_info: dict):
        self.check_updates_btn.setEnabled(True)
        self.app_update_worker = None

        if not update_info:
            self.update_status_label.setText("Could not check for updates (network unavailable?)")
            return

        if update_info.get("update_available"):
            self.update_status_label.setText(
                f"Update available: {update_info['latest_version']} (you have v{update_info['current_version']})"
            )
            reply = QMessageBox.question(
                self,
                "Update Available",
                f"A new version is available: {update_info['latest_version']}\n\n"
                "Open the download page?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if reply == QMessageBox.Yes:
                import webbrowser
                webbrowser.open(update_info["release_url"])
        else:
            self.update_status_label.setText(f"You're up to date (v{update_info.get('current_version', APP_VERSION)})")

    def _open_github(self):
        """Open the GitHub repository in the default browser."""
        import webbrowser
        webbrowser.open(f"https://github.com/{GITHUB_REPO}")

    def _update_config_value(self, key: str, value):
        """Update a single config value and save."""
        self.config[key] = value
        try:
            save_config(self.config)
        except Exception:
            pass  # Silently fail for individual updates

    def _safe_int(self, text: str, default: int) -> int:
        text = text.strip()
        if not text:
            return default
        try:
            return int(text)
        except ValueError:
            return default

    def _save_settings(self):
        """Save current settings to config."""
        try:
            # Update config dict
            output_dir = self.output_dir_input.text().strip()
            if not output_dir:
                output_dir = "music"

            self.config["output_dir"] = output_dir
            self.config["audio_format"] = self.format_combo.currentText()
            self.config["audio_bitrate"] = self.bitrate_combo.currentData()
            self.config["video_output_dir"] = self.video_output_dir_input.text().strip() or "videos"
            self.config["video_format"] = self.video_format_combo.currentData()
            self.config["embed_video_subs"] = self.embed_video_subs_check.isChecked()
            self.config["spotify_client_id"] = self.client_id_input.text().strip()
            self.config["sleep_between"] = self._safe_int(self.sleep_input.text(), 5)
            self.config["retry_attempts"] = self._safe_int(self.retry_input.text(), 3)
            self.config["ytdlp_extra_args"] = self.ytdlp_args_input.text().strip()
            self.config["ffmpeg_extra_args"] = self.ffmpeg_args_input.text().strip()
            self.config["enable_metadata_embedding"] = self.metadata_check.isChecked()
            self.config["metadata_template"] = self.template_combo.currentText()
            self.config["enable_musicbrainz_lookup"] = self.musicbrainz_check.isChecked()
            self.config["enable_lyrics_fetch"] = self.lyrics_check.isChecked()
            self.config["auto_backup"] = self.backup_check.isChecked()
            self.config["max_backups"] = self._safe_int(self.max_backups_input.text(), 10)
            self.config["auto_redownload_corrupted"] = self.auto_redownload_check.isChecked()
            self.config["ffmpeg_path"] = self.ffmpeg_path_input.text().strip()
            self.config["ytdlp_path"] = self.ytdlp_path_input.text().strip()

            # Validate
            is_valid, errors = validate_config(self.config)
            if not is_valid:
                QMessageBox.warning(
                    self,
                    "Validation Error",
                    "Invalid settings:\n" + "\n".join(errors)
                )
                return

            # Create output directory if it doesn't exist
            if output_dir and not os.path.isabs(output_dir):
                # For relative paths, create from current working directory
                os.makedirs(output_dir, exist_ok=True)
            elif output_dir:
                # For absolute paths, try to create
                os.makedirs(output_dir, exist_ok=True)

            # Save
            save_config(self.config)
            # Reload config to ensure fresh state
            self.config = load_config()
            self._load_values()  # Refresh UI to show saved values
            self.config_saved.emit()
            QMessageBox.information(self, "Success", "Settings saved successfully!")

        except ValueError as e:
            QMessageBox.warning(self, "Error", f"Invalid value: {e}")
        except PermissionError:
            QMessageBox.warning(
                self,
                "Permission Error",
                f"Cannot create output directory:\n{output_dir}\n\n"
                "Please choose a different location."
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")

    def _reset_to_defaults(self):
        """Reset all settings to defaults."""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            for key, value in DEFAULT_CONFIG.items():
                self.config[key] = value
            self._load_values()
            QMessageBox.information(self, "Reset", "Settings reset to defaults.")
