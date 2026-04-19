import argparse
import os
import shutil
import subprocess
import sys
from urllib.parse import urlparse

import internetarchive

from config import OUTPUT_DIR, STAGING_DIR

THUMBNAIL_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif"}


def parse_ia_url(url: str) -> tuple[str, str | None]:
    parsed = urlparse(url)
    if parsed.netloc != "archive.org":
        raise ValueError(f"Not an Internet Archive URL: {url}")

    parts = [p for p in parsed.path.strip("/").split("/") if p]
    if len(parts) < 2 or parts[0] != "details":
        raise ValueError(f"Cannot parse Internet Archive URL: {url}")

    identifier = parts[1]
    filename = parts[2] if len(parts) > 2 else None
    return identifier, filename


def is_remote(path: str) -> bool:
    return ":" in path


def select_files(identifier: str, format_pref: str, thumbs: bool = True) -> list[str] | None:
    """Return filenames to download for the given format preference.

    Returns None for 'all', which tells internetarchive to download everything.
    For 'flac': prefers .flac files, falls back to .mp3 if none exist.
    Thumbnails (jpg/jpeg/png/gif) are included by default unless thumbs=False.
    """
    if format_pref == "all":
        return None

    item = internetarchive.get_item(identifier)
    names = [f["name"] for f in item.files]

    flac = [n for n in names if n.lower().endswith(".flac")]
    mp3 = [n for n in names if n.lower().endswith(".mp3")]

    audio = mp3 if format_pref == "mp3" else (flac if flac else mp3)

    if thumbs:
        images = [n for n in names if os.path.splitext(n)[1].lower() in THUMBNAIL_EXTENSIONS]
        return audio + images

    return audio


def sync_to_dest(local_path: str, dest: str) -> None:
    """Sync a local directory to dest using rsync. Works for both local and SSH remotes."""
    item_name = os.path.basename(local_path)
    target = f"{dest}/{item_name}/"
    subprocess.run(
        ["rsync", "-avz", "--no-times", "--no-perms", "--inplace", "--progress", f"{local_path}/", target],
        check=True,
    )


def download_from_ia(
    identifier: str,
    filename: str | None = None,
    format_pref: str = "flac",
    thumbs: bool = True,
) -> str:
    """Download an IA item to staging, sync to OUTPUT_DIR, then clean up staging.

    Interrupted downloads leave files in STAGING_DIR so the next run resumes
    automatically — internetarchive skips files that are already the correct size.
    If filename is given, format_pref and thumbs are ignored.
    """
    files = [filename] if filename else select_files(identifier, format_pref, thumbs)

    staging_path = os.path.join(STAGING_DIR, identifier)
    os.makedirs(STAGING_DIR, exist_ok=True)

    internetarchive.download(identifier, files=files, destdir=STAGING_DIR, verbose=True)

    sync_to_dest(staging_path, OUTPUT_DIR)
    shutil.rmtree(staging_path)

    return f"{OUTPUT_DIR}/{identifier}"


def clean_staging() -> None:
    if os.path.exists(STAGING_DIR):
        shutil.rmtree(STAGING_DIR)
        print(f"Cleared {STAGING_DIR}")
    else:
        print(f"Nothing to clean ({STAGING_DIR} is already empty)")


def main(url: str, format_pref: str = "flac", thumbs: bool = True) -> None:
    identifier, filename = parse_ia_url(url)
    if filename:
        print(f"Downloading '{filename}' from '{identifier}'...")
    else:
        print(f"Downloading '{format_pref}' files from '{identifier}' (thumbs: {thumbs})...")
    try:
        path = download_from_ia(identifier, filename, format_pref, thumbs)
    except KeyboardInterrupt:
        print(f"\nInterrupted. Staged files kept at {STAGING_DIR}/{identifier} — run again to resume.")
        sys.exit(1)
    print(f"Done: {path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download media from Internet Archive")
    parser.add_argument("url", nargs="?", help="Internet Archive item or file URL")
    parser.add_argument(
        "--format",
        choices=["flac", "mp3", "all"],
        default="flac",
        dest="format_pref",
        help="Audio format to download (default: flac, falls back to mp3 if unavailable)",
    )
    parser.add_argument(
        "--no-thumbs",
        action="store_false",
        dest="thumbs",
        help="Skip thumbnails and images, download audio only",
    )
    parser.add_argument("--clean", action="store_true", help="Clear the staging directory and exit")
    args = parser.parse_args()

    if args.clean:
        clean_staging()
        sys.exit(0)

    if not args.url:
        parser.print_help()
        sys.exit(1)

    main(args.url, args.format_pref, args.thumbs)
