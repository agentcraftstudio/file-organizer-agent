# File Organizer Agent

Sort a messy folder into Documents, Images, Archives, Installers, Audio, Video and Other,
safely: dry run by default, an undo log for every move, and one command to put it all back.

Built with Claude Code on Ubuntu for the AgentCraft Studio video
*AI Agent Organizes 500 Messy Files on Linux (Claude Code)*. Python 3 standard library only.

## Try it on fake files first

```bash
python3 make_test_files.py ~/agent-test        # 500 placeholder files
python3 organize.py ~/agent-test               # dry run: shows the plan, moves nothing
python3 organize.py ~/agent-test --apply       # sorts the files and prints the undo command
python3 organize.py --undo ~/.local/state/file-organizer/undo-YYYYMMDD-HHMMSS.jsonl
```

## Prove the undo worked

```bash
find ~/agent-test -mindepth 1 -printf '%P\t%s\t%T@\n' | sort > before.txt   # before --apply
# ... --apply, then --undo ...
find ~/agent-test -mindepth 1 -printf '%P\t%s\t%T@\n' | sort | diff - before.txt && echo IDENTICAL
```

## What it will and won't do

- Moves top-level files only. Subfolders, hidden files and symlinks are left alone.
- Never deletes and never overwrites: a name clash becomes `name (1).ext`.
- Undo logs live in `~/.local/state/file-organizer/`, outside the folder being sorted.
- Sorts by extension only. It doesn't read file contents.

`spec.md` is the prompt that produced this. Run the checks with `python3 -m unittest -v`.

## License

MIT. See [LICENSE](LICENSE).
