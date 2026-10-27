#!/usr/bin/env python3
"""Sort the top-level files of a folder into subfolders by type.

    organize.py FOLDER               dry run: show the moves, change nothing
    organize.py FOLDER --apply       do the moves, writing an undo log
    organize.py --undo LOG           reverse a previous --apply
"""
import argparse
import json
import os
import sys
import time

CATEGORIES = {
    "Documents": "pdf doc docx odt rtf txt md csv xls xlsx ods ppt pptx odp epub pages key numbers",
    "Images": "jpg jpeg png gif bmp tif tiff webp heic svg ico raw cr2 nef psd",
    "Archives": "zip rar 7z tar gz tgz bz2 xz zst iso",
    "Installers": "exe msi dmg pkg deb rpm appimage apk snap flatpak",
    "Audio": "mp3 wav flac aac ogg m4a wma opus aiff",
    "Video": "mp4 mkv avi mov wmv flv webm m4v mpg mpeg 3gp",
}
EXT_TO_CATEGORY = {ext: cat for cat, exts in CATEGORIES.items() for ext in exts.split()}
OTHER = "Other"


def category_for(name):
    ext = os.path.splitext(name)[1].lstrip(".").lower()
    return EXT_TO_CATEGORY.get(ext, OTHER)


def free_name(name, taken):
    """Return `name`, or `name (1)`, `name (2)`... - whichever isn't in `taken`."""
    stem, ext = os.path.splitext(name)
    candidate, n = name, 0
    while candidate in taken:
        n += 1
        candidate = f"{stem} ({n}){ext}"
    return candidate


def make_plan(folder):
    """Return (folders_to_create, [(src, dst), ...]). Raises SystemExit on conflicts."""
    with os.scandir(folder) as it:
        files = sorted(e.name for e in it
                       if not e.name.startswith(".") and e.is_file(follow_symlinks=False))

    moves, taken = [], {}
    for name in files:
        cat = category_for(name)
        if cat not in taken:
            dest_dir = os.path.join(folder, cat)
            if os.path.lexists(dest_dir) and (os.path.islink(dest_dir) or not os.path.isdir(dest_dir)):
                sys.exit(f"Stopping: '{dest_dir}' exists and is not a folder. Nothing was moved.")
            taken[cat] = set(os.listdir(dest_dir)) if os.path.isdir(dest_dir) else set()
        new_name = free_name(name, taken[cat])
        taken[cat].add(new_name)
        moves.append((os.path.join(folder, name), os.path.join(folder, cat, new_name)))

    to_create = [os.path.join(folder, c) for c in taken if not os.path.isdir(os.path.join(folder, c))]
    return to_create, moves


def log_entry(log, entry):
    log.write(json.dumps(entry) + "\n")
    log.flush()
    os.fsync(log.fileno())


def move_no_overwrite(src, dst):
    if os.path.lexists(dst):
        raise FileExistsError(f"refusing to overwrite '{dst}'")
    os.rename(src, dst)


def apply(folder, to_create, moves, log_path):
    # Moving files changes folder mtimes, so remember them for --undo to restore.
    existing_dirs = [folder] + sorted({os.path.dirname(d) for _, d in moves} - set(to_create))
    with open(log_path, "x") as log:
        log_entry(log, {"op": "start", "folder": folder,
                        "dir_mtimes": {d: os.stat(d).st_mtime_ns for d in existing_dirs}})
        for d in to_create:
            log_entry(log, {"op": "mkdir", "path": d})
            os.mkdir(d)
        for src, dst in moves:
            log_entry(log, {"op": "move", "src": src, "dst": dst})
            move_no_overwrite(src, dst)
    print(f"Moved {len(moves)} files. Undo log: {log_path}")
    print(f"To reverse: {sys.argv[0]} --undo {log_path}")


def undo(log_path):
    with open(log_path) as f:
        entries = [json.loads(line) for line in f if line.strip()]
    restored = skipped = 0
    for e in reversed(entries):
        if e["op"] == "move":
            src, dst = e["src"], e["dst"]
            if not os.path.lexists(dst):
                print(f"SKIP (no longer at '{dst}'): {src}")
                skipped += 1
            elif os.path.lexists(src):
                print(f"SKIP (something already at original location): {src}")
                skipped += 1
            else:
                os.rename(dst, src)
                restored += 1
        elif e["op"] == "mkdir":
            try:
                os.rmdir(e["path"])
            except FileNotFoundError:
                pass
            except OSError:
                print(f"KEPT (not empty): {e['path']}")
        elif e["op"] == "start":
            for d, mtime in e.get("dir_mtimes", {}).items():
                if os.path.isdir(d):
                    os.utime(d, ns=(os.stat(d).st_atime_ns, mtime))
    print(f"Restored {restored} files, skipped {skipped}.")


def main():
    p = argparse.ArgumentParser(description="Sort a folder's files into subfolders by type.")
    p.add_argument("folder", nargs="?", help="folder to organize")
    p.add_argument("--apply", action="store_true", help="actually move files (default: dry run)")
    p.add_argument("--log", help="undo log path (default: organize-undo-<time>.jsonl in current dir)")
    p.add_argument("--undo", metavar="LOG", help="reverse the moves recorded in LOG")
    args = p.parse_args()

    if args.undo:
        return undo(args.undo)
    if not args.folder:
        p.error("folder is required unless --undo is given")

    folder = os.path.realpath(args.folder)
    if not os.path.isdir(folder):
        sys.exit(f"Not a folder: {folder}")
    to_create, moves = make_plan(folder)

    if not args.apply:
        for d in to_create:
            print(f"mkdir {d}")
        for src, dst in moves:
            print(f"move  {src} -> {dst}")
        print(f"\nDry run: {len(moves)} files would move. Re-run with --apply to do it.")
        return

    log_path = os.path.realpath(args.log or f"organize-undo-{time.strftime('%Y%m%d-%H%M%S')}.jsonl")
    if os.path.commonpath([folder, log_path]) == folder:
        sys.exit("The undo log must be stored outside the folder being organized.")
    apply(folder, to_create, moves, log_path)


if __name__ == "__main__":
    main()
