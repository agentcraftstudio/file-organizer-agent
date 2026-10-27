"""Checks the 'Done when' section of spec.md.  Run: python3 -m unittest -v"""
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest

import organize

HERE = os.path.dirname(os.path.abspath(__file__))


def snapshot(folder):
    """Every path under folder (and the folder itself) with size and mtime: the 'identical' check."""
    out = {("", None, os.stat(folder).st_mtime_ns)}
    for root, dirs, files in os.walk(folder):
        for name in dirs + files:
            path = os.path.join(root, name)
            st = os.lstat(path)
            out.add((os.path.relpath(path, folder), st.st_size if name in files else None, st.st_mtime_ns))
    return out


class OrganizeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.folder = os.path.join(self.tmp.name, "mess")
        self.log = os.path.join(self.tmp.name, "undo.jsonl")
        subprocess.run([sys.executable, os.path.join(HERE, "make_test_files.py"), self.folder, "--seed", "42"],
                       check=True, capture_output=True)

    def tearDown(self):
        self.tmp.cleanup()

    def run_main(self, *args):
        argv, sys.argv = sys.argv, ["organize.py", *args]
        try:
            with contextlib.redirect_stdout(io.StringIO()) as out:
                organize.main()
        finally:
            sys.argv = argv
        return out.getvalue()

    def logged_moves(self):
        with open(self.log) as f:
            return [(e["src"], e["dst"]) for e in map(json.loads, f) if e["op"] == "move"]

    def test_generator_makes_500_files(self):
        self.assertEqual(len(os.listdir(self.folder)), 500)

    def test_dry_run_changes_nothing(self):
        before = snapshot(self.folder)
        self.run_main(self.folder)
        self.assertEqual(snapshot(self.folder), before)

    def test_dry_run_matches_real_run(self):
        _, planned = organize.make_plan(os.path.realpath(self.folder))
        self.run_main(self.folder, "--apply", "--log", self.log)
        self.assertEqual(self.logged_moves(), planned)

    def test_apply_then_undo_is_identical(self):
        before = snapshot(self.folder)
        self.run_main(self.folder, "--apply", "--log", self.log)
        self.assertNotEqual(snapshot(self.folder), before)
        self.run_main("--undo", self.log)
        self.assertEqual(snapshot(self.folder), before)

    def test_never_overwrites(self):
        os.mkdir(os.path.join(self.folder, "Documents"))
        existing = os.path.join(self.folder, "Documents", "clash.pdf")
        with open(existing, "w") as f:
            f.write("old")
        with open(os.path.join(self.folder, "clash.pdf"), "w") as f:
            f.write("new")
        self.run_main(self.folder, "--apply", "--log", self.log)
        with open(existing) as f:
            self.assertEqual(f.read(), "old")
        with open(os.path.join(self.folder, "Documents", "clash (1).pdf")) as f:
            self.assertEqual(f.read(), "new")

    def test_leaves_hidden_files_symlinks_and_subfolders_alone(self):
        open(os.path.join(self.folder, ".hidden.pdf"), "w").close()
        os.symlink("/etc/hostname", os.path.join(self.folder, "link.txt"))
        os.mkdir(os.path.join(self.folder, "my stuff"))
        self.run_main(self.folder, "--apply", "--log", self.log)
        for name in (".hidden.pdf", "link.txt", "my stuff"):
            self.assertTrue(os.path.lexists(os.path.join(self.folder, name)), name)

    def test_stops_if_category_name_is_a_file(self):
        open(os.path.join(self.folder, "Images"), "w").close()
        before = snapshot(self.folder)
        with self.assertRaises(SystemExit):
            self.run_main(self.folder, "--apply", "--log", self.log)
        self.assertEqual(snapshot(self.folder), before)

    def test_refuses_undo_log_inside_folder(self):
        with self.assertRaises(SystemExit):
            self.run_main(self.folder, "--apply", "--log", os.path.join(self.folder, "undo.jsonl"))

    def test_undo_never_overwrites_a_returned_file(self):
        self.run_main(self.folder, "--apply", "--log", self.log)
        src, dst = self.logged_moves()[0]
        with open(src, "w") as f:
            f.write("new file with the same name")
        self.run_main("--undo", self.log)
        with open(src) as f:
            self.assertEqual(f.read(), "new file with the same name")
        self.assertTrue(os.path.exists(dst))


if __name__ == "__main__":
    unittest.main()
