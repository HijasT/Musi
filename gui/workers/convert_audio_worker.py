"""Audio format conversion worker: runs tools.convert_audio.convert_library
off the GUI thread."""

from PySide6.QtCore import QThread, Signal

from tools.convert_audio import convert_library


class ConvertAudioWorker(QThread):
    """Worker thread that converts the library to a target format/bitrate."""

    finished = Signal(dict)  # {"converted": int, "skipped": int, "failed": int, "error": str | None}

    def __init__(self, config: dict, target_format: str, target_bitrate: str,
                 delete_originals: bool = False, parent=None):
        super().__init__(parent)
        self.config = config
        self.target_format = target_format
        self.target_bitrate = target_bitrate
        self.delete_originals = delete_originals

    def run(self):
        result = convert_library(
            self.config, self.target_format, self.target_bitrate,
            delete_originals=self.delete_originals,
        )
        self.finished.emit(result or {"converted": 0, "skipped": 0, "failed": 0, "error": "Unknown error"})
