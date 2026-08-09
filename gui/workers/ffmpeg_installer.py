"""FFmpeg installer worker for downloading and extracting FFmpeg."""

import os
import sys
import zipfile
import shutil
import tempfile
from urllib.request import urlopen, Request
from urllib.error import URLError

from PySide6.QtCore import QThread, Signal


# FFmpeg download URLs (Windows builds from gyan.dev)
FFMPEG_URLS = {
    "win32": "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
}


class FFmpegInstallerWorker(QThread):
    """Worker thread for downloading and installing FFmpeg."""

    progress = Signal(int, str)  # progress percent, status message
    finished = Signal(bool, str)  # success, message

    def __init__(self, install_dir: str = None, parent=None):
        super().__init__(parent)
        self._cancelled = False

        # Default install directory is project_root/bin
        if install_dir is None:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.install_dir = os.path.join(project_root, "bin")
        else:
            self.install_dir = install_dir

    def cancel(self):
        """Cancel the download."""
        self._cancelled = True

    def run(self):
        """Run the FFmpeg installation."""
        try:
            # Check platform
            if sys.platform != "win32":
                self.finished.emit(False, "Automatic installation is only supported on Windows.\n"
                                   "Please install FFmpeg manually:\n"
                                   "  macOS: brew install ffmpeg\n"
                                   "  Linux: sudo apt install ffmpeg")
                return

            # Get download URL
            url = FFMPEG_URLS.get(sys.platform)
            if not url:
                self.finished.emit(False, f"No FFmpeg download available for {sys.platform}")
                return

            self.progress.emit(0, "Preparing download...")

            # Create temp directory for download
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, "ffmpeg.zip")

            try:
                # Download FFmpeg
                self.progress.emit(5, "Connecting to download server...")

                request = Request(url, headers={"User-Agent": "Musi/1.0"})
                response = urlopen(request, timeout=30)

                # Get file size if available
                total_size = int(response.headers.get("content-length", 0))
                downloaded = 0
                block_size = 1024 * 1024  # 1MB blocks

                self.progress.emit(10, "Downloading FFmpeg...")

                with open(zip_path, "wb") as f:
                    while True:
                        if self._cancelled:
                            self.finished.emit(False, "Download cancelled")
                            return

                        block = response.read(block_size)
                        if not block:
                            break

                        f.write(block)
                        downloaded += len(block)

                        if total_size > 0:
                            percent = int(10 + (downloaded / total_size) * 60)
                            size_mb = downloaded / (1024 * 1024)
                            total_mb = total_size / (1024 * 1024)
                            self.progress.emit(percent, f"Downloading... {size_mb:.1f} / {total_mb:.1f} MB")

                self.progress.emit(70, "Download complete. Extracting...")

                # Extract the zip file
                with zipfile.ZipFile(zip_path, "r") as zf:
                    # Find the ffmpeg executable in the archive
                    ffmpeg_files = [
                        name for name in zf.namelist()
                        if name.endswith("ffmpeg.exe") or name.endswith("ffprobe.exe")
                    ]

                    if not ffmpeg_files:
                        self.finished.emit(False, "FFmpeg executable not found in archive")
                        return

                    # Create install directory
                    os.makedirs(self.install_dir, exist_ok=True)

                    self.progress.emit(80, "Installing FFmpeg...")

                    # Extract ffmpeg and ffprobe
                    for file_path in ffmpeg_files:
                        if self._cancelled:
                            self.finished.emit(False, "Installation cancelled")
                            return

                        # Extract to temp, then move to install dir
                        zf.extract(file_path, temp_dir)
                        src = os.path.join(temp_dir, file_path)
                        dst = os.path.join(self.install_dir, os.path.basename(file_path))

                        # Remove existing file if present
                        if os.path.exists(dst):
                            os.remove(dst)

                        shutil.move(src, dst)

                self.progress.emit(95, "Verifying installation...")

                # Verify installation
                ffmpeg_path = os.path.join(self.install_dir, "ffmpeg.exe")
                if os.path.exists(ffmpeg_path):
                    self.progress.emit(100, "FFmpeg installed successfully!")
                    self.finished.emit(True, f"FFmpeg installed to:\n{self.install_dir}")
                else:
                    self.finished.emit(False, "Installation verification failed")

            finally:
                # Clean up temp directory
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except Exception:
                    pass

        except URLError as e:
            self.finished.emit(False, f"Download failed: {e.reason}")
        except zipfile.BadZipFile:
            self.finished.emit(False, "Downloaded file is corrupted")
        except PermissionError:
            self.finished.emit(False, f"Permission denied writing to:\n{self.install_dir}")
        except Exception as e:
            self.finished.emit(False, f"Installation failed: {str(e)}")


def check_ffmpeg_installed() -> tuple[bool, str]:
    """Check if FFmpeg is installed in the expected location."""
    from utils.ffmpeg import check_ffmpeg_available
    return check_ffmpeg_available()
