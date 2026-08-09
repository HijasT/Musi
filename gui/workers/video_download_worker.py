"""Video download worker: runs downloader.video_downloader.download_video
off the GUI thread. Standalone (not part of the audio DownloadQueue), since
video downloads aren't audio-format/metadata-embedding operations."""

from PySide6.QtCore import QThread, Signal

from downloader.video_downloader import download_video


class VideoDownloadWorker(QThread):
    """Worker thread that downloads a single video via yt-dlp."""

    finished = Signal(bool, str)  # success, error message (empty on success)

    def __init__(self, url: str, output_dir: str, config: dict, parent=None):
        super().__init__(parent)
        self.url = url
        self.output_dir = output_dir
        self.config = config

    def run(self):
        success, _file_path, error = download_video(
            self.url, self.output_dir, config=self.config, confirm=False
        )
        self.finished.emit(success, error or "")
