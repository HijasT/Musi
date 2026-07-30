import re
import unicodedata


def normalize_match_key(s: str) -> str:
    """Normalize a string for filesystem-safe filename matching.

    yt-dlp sanitizes reserved characters (: * / \\ < > | " ?) when writing files,
    and the exact replacement (dash, space, '#', full-width unicode, ...) varies by
    version/platform. Stripping all punctuation/whitespace after NFKC normalization
    (which folds full-width variants back to their ASCII form) lets us match a
    track's expected "artist - title" against whatever actually landed on disk.
    """
    s = unicodedata.normalize("NFKC", s or "")
    return re.sub(r"[\W_]+", "", s, flags=re.UNICODE).lower()
