#!/usr/bin/env python3
"""Sort the files in a folder into subfolders by type. See spec.md.

    python3 organize.py ~/Downloads             # dry run: print the plan, change nothing
    python3 organize.py ~/Downloads --apply     # move files and write an undo log
    python3 organize.py --undo LOGFILE          # put everything back
"""
import argparse
import json
import os
import sys
import time

CATEGORIES = {
    "Documents": {".pdf", ".doc", ".docx", ".odt", ".rtf", ".txt", ".md", ".xls", ".xlsx",
                  ".ods", ".csv", ".ppt", ".pptx", ".odp", ".epub"},
    "Images": {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".tif", ".tiff", ".heic"},
    "Archives": {".zip", ".tar", ".gz", ".tgz", ".bz2", ".xz", ".7z", ".rar"},
    "Installers": {".deb", ".rpm", ".appimage", ".snap", ".flatpak", ".run", ".sh"},
    "Audio": {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".opus", ".aac"},
    "Video": {".mp4", ".mkv", ".mov", ".webm", ".avi", ".m4v"},
}
OTHER = "Other"
LOG_DIR = os.path.expanduser("~/.local/state/file-organizer")


def category_for(name):
    ext = os.path.splitext(name)[1].lower()
    for category, exts in CATEGORIES.items():
        if ext in exts:
            return category
    return OTHER


def free_name(directory, name, taken):
    """Return a name in `directory` that doesn't exist on disk and isn't already planned."""
    stem, ext = os.path.splitext(name)
    candidate, n = name, 1
    while os.path.lexists(os.path.join(directory, candidate)) or os.path.join(directory, candidate) in taken:
        candidate = f"{stem} ({n}){ext}"
        n += 1
    return candidate


def plan(folder):
    """Work out every move before touching anything. Dry run and real run both use this."""
    moves, taken = [], set()
    for name in sorted(os.listdir(folder)):
        src = os.path.join(folder, name)
        if name.startswith(".") or os.path.islink(src) or not os.path.isfile(src):
            continue
        dest_dir = os.path.join(folder, category_for(name))
        if os.path.lexists(dest_dir) and not os.path.isdir(dest_dir):
            sys.exit(f"Stopping: '{dest_dir}' exists and is not a folder. Nothing was moved.")
        dst = os.path.join(dest_dir, free_name(dest_dir, name, taken))
        taken.add(dst)
        moves.append((src, dst))
    return moves


def log_entry(log, entry):
    log.write(json.dumps(entry) + "\n")
    log.flush()
    os.fsync(log.fileno())


def apply(folder, moves):
    os.makedirs(LOG_DIR, exist_ok=True)
    log_path = os.path.join(LOG_DIR, time.strftime("undo-%Y%m%d-%H%M%S.jsonl"))
    with open(log_path, "x") as log:
        log_entry(log, {"op": "start", "folder": folder})
        moved = 0
        for src, dst in moves:
            dest_dir = os.path.dirname(dst)
            if not os.path.isdir(dest_dir):
                os.mkdir(dest_dir)
                log_entry(log, {"op": "mkdir", "path": dest_dir})
            if os.path.lexists(dst):  # appeared since planning: never overwrite
                print(f"SKIP  {src} (destination appeared: {dst})")
                continue
            os.rename(src, dst)
            log_entry(log, {"op": "move", "src": src, "dst": dst})
            moved += 1
    print(f"\nMoved {moved} files. Undo log: {log_path}")
    print(f"To undo: python3 {sys.argv[0]} --undo {log_path}")


def undo(log_path):
    with open(log_path) as f:
        entries = [json.loads(line) for line in f if line.strip()]
    restored = skipped = 0
    for e in reversed(entries):
        if e["op"] == "move":
            if not os.path.lexists(e["dst"]) or os.path.lexists(e["src"]):
                print(f"SKIP  {e['dst']} (missing, or original location is taken)")
                skipped += 1
                continue
            os.rename(e["dst"], e["src"])
            restored += 1
        elif e["op"] == "mkdir":
            try:
                os.rmdir(e["path"])  # only succeeds if empty
            except OSError:
                print(f"KEEP  {e['path']} (not empty)")
    print(f"\nRestored {restored} files, skipped {skipped}.")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("folder", nargs="?")
    p.add_argument("--apply", action="store_true", help="actually move files (default is a dry run)")
    p.add_argument("--undo", metavar="LOGFILE", help="reverse a previous --apply run")
    args = p.parse_args()

    if args.undo:
        return undo(args.undo)
    if not args.folder:
        p.error("give a folder to organize, or --undo LOGFILE")
    folder = os.path.abspath(os.path.expanduser(args.folder))
    if not os.path.isdir(folder):
        sys.exit(f"Not a folder: {folder}")

    moves = plan(folder)
    for src, dst in moves:
        print(f"{'MOVE' if args.apply else 'WOULD MOVE'}  {os.path.relpath(src, folder)}  ->  {os.path.relpath(dst, folder)}")
    if not moves:
        print("Nothing to organize.")
    elif args.apply:
        apply(folder, moves)
    else:
        print(f"\nDry run: {len(moves)} files would move. Nothing changed. Add --apply to do it.")


if __name__ == "__main__":
    main()
