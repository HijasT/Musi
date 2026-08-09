import json
import questionary
from constants import AUDIO_BITRATE_OPTIONS
from utils.logger import log_success, log_error

def choose_audio_bitrate(config):
    """
    Lets user choose the download audio bitrate/quality, showing the active one first.
    """
    try:
        current_bitrate = config.get("audio_bitrate", "320k")
        choices = [
            f"{bitrate} - {desc}" + (" (active)" if bitrate == current_bitrate else "")
            for bitrate, desc in AUDIO_BITRATE_OPTIONS.items()
        ]

        choice = questionary.select(
            "Select download audio bitrate:",
            choices=choices
        ).ask()

        if not choice:
            return

        new_bitrate = choice.split()[0].strip()
        config["audio_bitrate"] = new_bitrate

        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        log_success(f"Audio bitrate updated to: {new_bitrate}")

    except Exception as e:
        log_error(f"Failed to update audio bitrate: {e}")
