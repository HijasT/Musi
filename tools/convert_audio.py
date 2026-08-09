import os
import subprocess
import questionary
from constants import VALID_AUDIO_EXTENSIONS, AUDIO_BITRATE_OPTIONS
from utils.logger import log_info, log_success, log_error, log_warning


def convert_library(config: dict, target_format: str, target_bitrate: str, delete_originals: bool = False) -> dict:
    """
    Converts audio files in the music library to target_format/target_bitrate using ffmpeg.
    Keeps originals unless delete_originals is True. Writes converted files alongside the
    source (or with a 'converted_' prefix if a same-named file already exists).

    Returns a dict: {"converted": int, "skipped": int, "failed": int, "error": str | None}
    """
    try:
        music_dir = config.get("output_dir", "music")
        if not os.path.exists(music_dir):
            log_error(f"Music folder not found: {music_dir}")
            return {"converted": 0, "skipped": 0, "failed": 0, "error": f"Music folder not found: {music_dir}"}

        target_ext = f".{target_format.strip('.')}"
        converted_count = 0
        skipped_count = 0
        failed_count = 0

        for root, _, files in os.walk(music_dir):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext not in VALID_AUDIO_EXTENSIONS or ext == target_ext:
                    continue

                src_path = os.path.join(root, file)
                stem = os.path.splitext(file)[0]
                dest_path = os.path.join(root, f"{stem}{target_ext}")

                if os.path.exists(dest_path):
                    dest_path = os.path.join(root, f"converted_{stem}{target_ext}")
                    if os.path.exists(dest_path):
                        skipped_count += 1
                        log_warning(f"Skipping {file}: target file already exists")
                        continue

                cmd = ["ffmpeg", "-y", "-i", src_path, "-b:a", target_bitrate, dest_path]
                try:
                    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    if result.returncode == 0 and os.path.exists(dest_path):
                        converted_count += 1
                        log_info(f"Converted: {file} -> {os.path.basename(dest_path)}")
                        if delete_originals:
                            os.remove(src_path)
                    else:
                        failed_count += 1
                        log_error(f"Failed to convert: {file}")
                except Exception as e:
                    failed_count += 1
                    log_error(f"Error converting {file}: {e}")

        log_success(
            f"Conversion complete. Converted {converted_count}, skipped {skipped_count}, failed {failed_count}."
        )
        return {"converted": converted_count, "skipped": skipped_count, "failed": failed_count, "error": None}

    except Exception as e:
        log_error(f"Error during audio conversion: {e}")
        return {"converted": 0, "skipped": 0, "failed": 0, "error": str(e)}


def convert_audio(config: dict):
    """Interactive CLI entry point: prompts for target format/bitrate, then converts."""
    format_choices = sorted(ext.strip(".") for ext in VALID_AUDIO_EXTENSIONS)
    target_format = questionary.select(
        "Convert library to which format?",
        choices=format_choices,
    ).ask()
    if not target_format:
        return

    bitrate_choices = [f"{b} - {d}" for b, d in AUDIO_BITRATE_OPTIONS.items()]
    bitrate_choice = questionary.select(
        "Target bitrate:",
        choices=bitrate_choices,
    ).ask()
    if not bitrate_choice:
        return
    target_bitrate = bitrate_choice.split()[0].strip()

    delete_originals = questionary.confirm(
        "Delete original files after successful conversion?", default=False
    ).ask()

    convert_library(config, target_format, target_bitrate, delete_originals=bool(delete_originals))
