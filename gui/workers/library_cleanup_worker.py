"""Library cleanup worker: removes corrupted/empty audio files and (optionally)
re-queues a redownload for each one, without blocking the GUI thread."""

from PySide6.QtCore import QThread, Signal

from tools.library_cleanup import library_cleanup


class LibraryCleanupWorker(QThread):
    """Worker thread that runs library_cleanup() off the GUI thread."""

    finished = Signal(dict)  # {"removed": int, "redownloaded": int, "skipped": int, "error": str | None}

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config

    def run(self):
        result = library_cleanup(self.config)
        self.finished.emit(result or {"removed": 0, "redownloaded": 0, "skipped": 0, "error": "Unknown error"})
