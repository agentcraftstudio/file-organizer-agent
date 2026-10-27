# File Organizer Agent

Sort a messy folder into Documents, Images, Archives, Installers, Audio, Video and Other,
safely: dry run by default, an undo log for every move, and one command to put it all back.

Built with Claude Code on Ubuntu for the AgentCraft Studio video
*AI Agent Organizes 500 Messy Files on Linux (Claude Code)*. Python 3 standard library only.

## Try it on fake files first

```bash
python3 make_test_files.py ~/agent-test --seed 42          # 500 placeholder files
python3 organize.py ~/agent-test                           # dry run: shows the plan, moves nothing
python3 organize.py ~/agent-test --apply --log undo.jsonl  # sorts the files, writes the undo log
python3 organize.py --undo undo.jsonl                      # puts everything back
```

## Prove the undo worked

```bash
find ~/agent-test -printf '%P\t%s\t%T@\n' | sort > before.txt   # before --apply
# ... --apply, then --undo ...
find ~/agent-test -printf '%P\t%s\t%T@\n' | sort | diff - before.txt && echo IDENTICAL
```

## What it will and won't do

- Moves top-level files only. Subfolders, hidden files and symlinks are left alone.
- Never deletes and never overwrites: a name clash becomes `name (1).ext`.
- The undo log must live outside the folder being sorted (it refuses otherwise). Default: `organize-undo-<time>.jsonl` in the current directory.
- Undo also restores folder timestamps, so the folder really is identical afterwards.
- Sorts by extension only. It doesn't read file contents.

`spec.md` is the prompt that produced this: the code here is exactly what Claude Code wrote on camera. Run the checks with `python3 -m unittest -v`.

## License

MIT. See [LICENSE](LICENSE).
