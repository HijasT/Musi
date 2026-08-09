"""Favorites menu: manage and quick-download saved links/searches."""

import questionary

from utils.logger import log_info, log_warning
from managers.favorites_manager import load_favorites, add_favorite, remove_favorite


def _label(fav: dict) -> str:
    kind_label = "link" if fav.get("kind") == "link" else "search"
    return f"{fav['name']} ({kind_label}: {fav['value']})"


def favorites_menu(config: dict) -> None:
    """Displays the Favorites menu: download, add, or remove saved entries."""
    from downloader.base_downloader import download_track
    from downloader.youtube_link_downloader import download_from_link, download_from_playlist

    while True:
        favorites = load_favorites()

        choices = [_label(f) for f in favorites]
        choices += ["Add a favorite", "Remove a favorite", "Back"]

        choice = questionary.select(
            "⭐ Favorites — quick re-download saved links/searches:",
            choices=choices,
        ).ask()

        if not choice or choice == "Back":
            break

        elif choice == "Add a favorite":
            kind = questionary.select(
                "What are you saving?",
                choices=[
                    questionary.Choice(title="A link (YouTube video/playlist URL)", value="link"),
                    questionary.Choice(title="A search (Artist - Track)", value="search"),
                ],
            ).ask()
            if not kind:
                continue

            value = questionary.text(
                "Paste the URL:" if kind == "link" else "Enter 'Artist - Track':"
            ).ask()
            value = (value or "").strip()
            if not value:
                log_warning("No value provided.")
                continue

            name = questionary.text("Name this favorite:", default=value[:50]).ask()
            name = (name or "").strip() or value[:50]

            record = add_favorite(name, value, kind)
            if record:
                log_info(f"Saved favorite: {name}")
            else:
                log_info("Favorite already exists — name updated.")

        elif choice == "Remove a favorite":
            if not favorites:
                log_info("No favorites to remove.")
                continue
            target = questionary.select(
                "Select a favorite to remove:",
                choices=[questionary.Choice(title=_label(f), value=f["id"]) for f in favorites],
            ).ask()
            if target and remove_favorite(target):
                log_info("Favorite removed.")

        else:
            # A favorite label was selected directly — download it.
            fav = favorites[choices.index(choice)]
            if fav["kind"] == "link":
                url = fav["value"]
                if "playlist" in url.lower():
                    download_from_playlist(
                        url, config["output_dir"], config["audio_format"],
                        config["sleep_between"], config=config,
                    )
                else:
                    download_from_link(url, config["output_dir"], config["audio_format"], config=config)
            else:
                artist, _, track = fav["value"].partition(" - ")
                artist = artist.strip() or "Unknown Artist"
                track = (track or fav["value"]).strip()
                download_track(
                    artist, track, config["output_dir"], config["audio_format"],
                    config["sleep_between"], config=config,
                )
