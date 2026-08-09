"""Background worker that checks for a newer Musi release without blocking
the GUI thread or delaying startup."""

from PySide6.QtCore import QThread, Signal

from tools.app_update_checker import check_app_updates


class AppUpdateCheckWorker(QThread):
    """Worker thread that checks GitHub Releases for a newer Musi version."""

    finished = Signal(dict)  # update_info dict, or {} if the check failed

    def run(self):
        result = check_app_updates()
        self.finished.emit(result or {})
