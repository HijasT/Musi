import os
import subprocess
from constants import VALID_AUDIO_EXTENSIONS
from utils.logger import log_info, log_success, log_error, log_warning

def is_file_corrupted(file_path):
    """
    Uses ffmpeg to check if the file is corrupted.
    Returns True if corrupted or unreadable.
    """
    try:
        cmd = ["ffmpeg", "-v", "error", "-i", file_path, "-f", "null", "-"]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.returncode != 0
    except Exception:
        return True


def _parse_artist_track(filename: str):
    """Parse the 'Artist - Title.ext' filename convention used by the downloader.

    Returns (artist, track) or None if the filename doesn't follow that convention.
    """
    try:
        artist, title_ext = filename.split(" - ", 1)
        title = title_ext.rsplit(".", 1)[0]
        artist, title = artist.strip(), title.strip()
        if artist and title:
            return artist, title
    except Exception:
        pass
    return None


def library_cleanup(config):
    """
    Removes broken music files: unreadable, 0 bytes, or corrupted.
    When auto_redownload_corrupted is enabled (default), immediately re-queues
    a redownload for each removed file whose filename can be parsed back into
    an artist/track pair, in the same folder it was removed from.

    Returns a dict: {"removed": int, "redownloaded": int, "skipped": int, "error": str | None}
    """
    try:
        music_dir = config.get("output_dir", "music")

        if not os.path.exists(music_dir):
            log_error(f"Music folder not found: {music_dir}")
            return {"removed": 0, "redownloaded": 0, "skipped": 0, "error": f"Music folder not found: {music_dir}"}

        auto_redownload = config.get("auto_redownload_corrupted", True)

        removed_count = 0
        redownloaded_count = 0
        skipped_count = 0

        for root, _, files in os.walk(music_dir):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in VALID_AUDIO_EXTENSIONS:
                    file_path = os.path.join(root, file)
                    if os.path.getsize(file_path) == 0 or is_file_corrupted(file_path):
                        try:
                            os.remove(file_path)
                            removed_count += 1
                            log_info(f"Removed broken file: {file_path}")
                        except Exception as e:
                            log_error(f"Failed to remove {file_path}: {e}")
                            continue

                        if not auto_redownload:
                            continue

                        parsed = _parse_artist_track(file)
                        if not parsed:
                            skipped_count += 1
                            log_warning(f"Cannot auto-redownload {file}: filename doesn't match 'Artist - Title' pattern")
                            continue

                        artist, track = parsed
                        try:
                            from downloader.base_downloader import download_track
                            log_info(f"Auto-redownloading: {artist} - {track}")
                            download_track(
                                artist,
                                track,
                                root,
                                config.get("audio_format", "mp3"),
                                config.get("sleep_between", 5),
                                config=config,
                            )
                            redownloaded_count += 1
                        except Exception as e:
                            log_error(f"Auto-redownload failed for {artist} - {track}: {e}")

        summary = f"Library cleanup complete. Removed {removed_count} broken files."
        if auto_redownload:
            summary += f" Redownloaded {redownloaded_count}, skipped {skipped_count} (unparseable filename)."
        log_success(summary)

        return {
            "removed": removed_count,
            "redownloaded": redownloaded_count,
            "skipped": skipped_count,
            "error": None,
        }

    except Exception as e:
        log_error(f"Error during library cleanup: {e}")
        return {"removed": 0, "redownloaded": 0, "skipped": 0, "error": str(e)}
