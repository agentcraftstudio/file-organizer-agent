# Spec: File Organizer

## Goal

Sort every file in one folder into subfolders by type:
Documents, Images, Archives, Installers, Audio, Video, and Other.

Files whose type isn't recognised, including files with no extension, go to Other.

## Rules

- Never delete anything.
- Never overwrite anything. If a file with the same name already exists in the destination,
  rename the incoming file (`report.pdf` → `report (1).pdf`) instead of replacing the old one.
- Only touch files at the top level of the folder passed in. Leave subfolders, hidden files
  (names starting with `.`) and symlinks alone. Never touch anything outside that folder.
- If a category folder can't be created because a file already has that name, stop before
  moving anything.

## Safety features

- **Dry run by default.** Without `--apply`, print every move the script would make and change nothing.
- **Undo log.** With `--apply`, record every folder created and every file moved in an undo log
  stored outside the sorted folder. Write each entry to disk before starting the next move.
- **Undo command.** `--undo LOG` reads the log and reverses it in reverse order: it moves every
  file back and removes the category folders it created, if they're empty. It never overwrites
  a file that has reappeared in the original location; it skips that file and reports it.

## Done when

- The dry run lists exactly the moves the real run makes.
- After `--apply` then `--undo`, the folder is identical to how it started: same names, sizes
  and modification times.
- Python 3 standard library only. No packages to install.
