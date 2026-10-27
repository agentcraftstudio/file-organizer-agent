#!/usr/bin/env python3
"""Create a folder of fake files that looks like a messy Downloads folder.

    python3 make_test_files.py ~/agent-test          # 500 files
    python3 make_test_files.py ~/agent-test -n 200   # any count

The files are small text placeholders: the extensions are real, the contents are not.
Same seed, same files, so every take of the recording starts from the same mess.
"""
import argparse
import os
import random
import sys
import time

STEMS = [
    "invoice", "receipt", "report", "notes", "resume", "contract", "slides", "budget",
    "Screenshot from 2026-10-02", "IMG", "photo", "wallpaper", "logo", "scan",
    "backup", "project", "dataset", "setup", "installer", "podcast", "voice memo",
    "recording", "lecture", "final", "final_v2_REAL", "untitled", "download", "meeting",
]
EXTS = [
    ".pdf", ".docx", ".txt", ".md", ".xlsx", ".csv", ".pptx", ".odt",
    ".png", ".jpg", ".JPG", ".jpeg", ".gif", ".webp", ".svg",
    ".zip", ".tar.gz", ".7z", ".rar",
    ".deb", ".AppImage", ".sh", ".rpm",
    ".mp3", ".wav", ".m4a", ".flac",
    ".mp4", ".mkv", ".mov", ".webm",
    ".json", ".log", ".ics", ".torrent",  # these land in Other
    "",                                   # no extension
]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("folder")
    p.add_argument("-n", "--count", type=int, default=500)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    folder = os.path.abspath(os.path.expanduser(args.folder))
    if os.path.exists(folder) and os.listdir(folder):
        sys.exit(f"{folder} is not empty. Pick a new folder so nothing real is mixed in.")
    os.makedirs(folder, exist_ok=True)

    rng = random.Random(args.seed)
    now = time.time()
    made = set()
    while len(made) < args.count:
        stem = rng.choice(STEMS)
        suffix = rng.choice(["", f"_{rng.randint(1, 999):03d}", f" ({rng.randint(1, 4)})", f"-{rng.randint(2019, 2026)}"])
        name = f"{stem}{suffix}{rng.choice(EXTS)}"
        if name in made:
            continue
        path = os.path.join(folder, name)
        with open(path, "w") as f:
            f.write(f"placeholder file: {name}\n" * rng.randint(1, 40))
        # spread modification times over the past year so the folder looks lived-in
        mtime = now - rng.randint(0, 365 * 24 * 3600)
        os.utime(path, (mtime, mtime))
        made.add(name)

    print(f"Created {len(made)} files in {folder}")


if __name__ == "__main__":
    main()
