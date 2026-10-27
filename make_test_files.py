#!/usr/bin/env python3
"""Create a NEW folder full of fake files named like a messy Downloads folder.

    make_test_files.py FOLDER [-n 500] [--seed 1]
"""
import argparse
import os
import random
import sys
import time

STEMS = ["invoice", "report_final", "report_final_FINAL", "resume", "Screenshot 2026-03-14 at 10.22.31",
         "IMG_4821", "DSC00172", "photo", "setup", "installer_v2.3.1", "song", "podcast_ep12",
         "meeting recording", "backup", "project-files", "notes", "untitled", "download", "tax_2025",
         "Copy of budget", "vacation", "lecture 3", "README", "Zoom_installer", "wallpaper"]
EXTS = [".pdf", ".docx", ".txt", ".xlsx", ".csv", ".pptx", ".jpg", ".JPG", ".png", ".jpeg", ".gif",
        ".heic", ".zip", ".tar.gz", ".7z", ".rar", ".exe", ".msi", ".dmg", ".deb", ".mp3", ".wav",
        ".flac", ".mp4", ".mkv", ".mov", ".xyz", ".torrent", ".crdownload", ""]
SUFFIXES = ["", "", "", " (1)", " (2)", " copy", "-1", "_v2", " - Copy"]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("folder")
    p.add_argument("-n", type=int, default=500, help="number of files (default 500)")
    p.add_argument("--seed", type=int, help="random seed for repeatable output")
    args = p.parse_args()

    if os.path.exists(args.folder) and (not os.path.isdir(args.folder) or os.listdir(args.folder)):
        sys.exit(f"Refusing: '{args.folder}' exists and is not an empty folder.")
    os.makedirs(args.folder, exist_ok=True)

    rng = random.Random(args.seed)
    names = set()
    while len(names) < args.n:
        name = rng.choice(STEMS) + rng.choice(SUFFIXES) + rng.choice(EXTS)
        if name in names:  # make duplicates unique, like "IMG_4821_5532.jpg"
            stem, ext = os.path.splitext(name)
            name = f"{stem}_{rng.randint(1, 99999)}{ext}"
        names.add(name)

    now = time.time()
    for name in sorted(names):
        path = os.path.join(args.folder, name)
        with open(path, "x") as f:
            f.write(f"fake file: {name}\n" * rng.randint(1, 50))
        mtime = now - rng.randint(0, 365 * 24 * 3600)
        os.utime(path, (mtime, mtime))
    print(f"Created {len(names)} files in {os.path.abspath(args.folder)}")


if __name__ == "__main__":
    main()
