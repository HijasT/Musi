import os
import glob
import subprocess
import json
import questionary
from utils.logger import log_info, log_success, log_error
from utils.ytdlp_args import build_extra_ytdlp_args


def get_video_info(url):
    """
    Fetches video/playlist metadata using yt-dlp in JSON format.
    """
    try:
        result = subprocess.run(
            ["yt-dlp", "-j", "--flat-playlist", url],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            log_error(f"Failed to fetch info for {url}")
            return None

        lines = result.stdout.strip().split("\n")
        data = []
        for line in lines:
            if line.strip():
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return data
    except Exception as e:
        log_error(f"Error fetching info: {e}")
        return None


def download_video(url, output_dir, config=None, confirm=True):
    """
    Download a full video (merged best video + best audio) from any
    yt-dlp-supported site — YouTube, TikTok, Instagram, Twitter/X, Reddit,
    Twitch, and hundreds more. Unlike the rest of Chaos Media Downloader, this
    keeps the video track rather than extracting audio only.

    Set confirm=False for non-interactive callers (e.g. the GUI, which
    should confirm via its own dialog before calling this).

    Returns (success: bool, file_path: Optional[str], error: Optional[str])
    """
    log_info(f"Fetching info for video: {url}")
    data = get_video_info(url)

    title = "video"
    if data and len(data) > 0:
        title = data[0].get("title", "video")

    if confirm:
        if not questionary.confirm(f"Download this video?\n\nTitle: {title}").ask():
            log_info("Cancelled by user.")
            return False, None, "Cancelled by user"

    os.makedirs(output_dir, exist_ok=True)

    video_format = (config or {}).get("video_format", "mp4")

    cmd = [
        "yt-dlp",
        url,
        "-f", "bv*+ba/b",
        "--merge-output-format", video_format,
        "-o", os.path.join(output_dir, "%(title)s.%(ext)s"),
        "--embed-metadata",
        "--embed-thumbnail",
    ]
    if (config or {}).get("embed_video_subs", True):
        cmd += ["--write-auto-subs", "--embed-subs"]
    cmd.extend(build_extra_ytdlp_args(config))

    try:
        result = subprocess.run(cmd)
        if result.returncode == 0:
            log_success(f"Downloaded video: {title}")

            # Best-effort: find the file we just created, for history logging.
            file_path = None
            try:
                matches = glob.glob(os.path.join(output_dir, f"*.{video_format}"))
                if matches:
                    file_path = max(matches, key=os.path.getmtime)
            except OSError:
                pass

            try:
                from managers.history_manager import log_video_download
                log_video_download(title, url, file_path=file_path)
            except Exception:
                pass

            return True, file_path, None
        else:
            log_error(f"Failed to download video: {title}")
            return False, None, "yt-dlp exited with an error"
    except FileNotFoundError:
        return False, None, "yt-dlp not found. Please install yt-dlp."
    except Exception as e:
        log_error(f"Error downloading video {title}: {e}")
        return False, None, str(e)
