import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
PLUGIN_COPY = "plugins/ukr-text-guard/skills/ukr-text-guard/references/lexicon.md"


def git(root, *args, env=None, check=True):
    return subprocess.run(
        ["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t", *args],
        capture_output=True, text=True, env=env, check=check,
    )


class PreCommitHookTest(unittest.TestCase):
    """Хук у тимчасовому репозиторії з копіями файлів цього репозиторію."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        git(self.root, "init", "-q")
        for top in ("shared", "plugins", "tools", ".githooks"):
            shutil.copytree(REPO / top, self.root / top, ignore=shutil.ignore_patterns("__pycache__", "tests"))
        git(self.root, "config", "core.hooksPath", ".githooks")
        git(self.root, "add", "-A")

    def commit(self, env=None):
        return git(self.root, "commit", "-q", "-m", "x", env=env, check=False)

    def test_clean_commit_is_allowed(self):
        done = self.commit()
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)

    def test_staged_divergence_is_refused_with_the_report(self):
        path = self.root / PLUGIN_COPY
        path.write_bytes(path.read_bytes() + b"x")
        git(self.root, "add", PLUGIN_COPY)
        done = self.commit()
        self.assertNotEqual(done.returncode, 0)
        out = done.stdout + done.stderr
        self.assertIn("error shared.differing: references/lexicon.md ukr-text-guard", out)
        self.assertIn("refused", out)

    def test_divergence_only_in_working_folder_is_allowed(self):
        path = self.root / PLUGIN_COPY
        path.write_bytes(path.read_bytes() + b"x")  # не додано до індексу
        self.assertEqual(self.commit().returncode, 0)

    def test_check_that_cannot_run_refuses_with_reason_and_bypass(self):
        (self.root / "shared" / "carry.json").write_text("{not json", encoding="utf-8")
        git(self.root, "add", "shared/carry.json")
        done = self.commit()
        self.assertNotEqual(done.returncode, 0)
        out = done.stdout + done.stderr
        self.assertIn("could not run", out)
        self.assertIn("carry.json", out)
        self.assertIn("git commit --no-verify", out)

    def test_broken_script_refuses_with_bypass(self):
        (self.root / "tools" / "shared_sync.py").unlink()
        done = self.commit()
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("could not run", done.stdout + done.stderr)
        self.assertIn("git commit --no-verify", done.stdout + done.stderr)

    def test_no_working_interpreter_refuses_with_bypass(self):
        stubs = self.root.parent / (self.root.name + "-stubs")
        stubs.mkdir()
        self.addCleanup(shutil.rmtree, str(stubs), True)
        for name in ("python3", "python", "py"):
            (stubs / name).write_text("#!/bin/sh\nexit 1\n", encoding="utf-8", newline="\n")
            os.chmod(stubs / name, 0o755)
        env = dict(os.environ, PATH=str(stubs) + os.pathsep + os.environ["PATH"])
        done = self.commit(env=env)
        self.assertNotEqual(done.returncode, 0)
        out = done.stdout + done.stderr
        self.assertIn("could not run", out)
        self.assertIn("no working Python found", out)
        self.assertIn("git commit --no-verify", out)

    def test_no_verify_bypasses_the_hook(self):
        path = self.root / PLUGIN_COPY
        path.write_bytes(path.read_bytes() + b"x")
        git(self.root, "add", PLUGIN_COPY)
        done = git(self.root, "commit", "-q", "--no-verify", "-m", "x", check=False)
        self.assertEqual(done.returncode, 0)

    def test_commit_touching_only_readme_still_runs_the_check(self):
        self.assertEqual(self.commit().returncode, 0)  # чиста база
        path = self.root / PLUGIN_COPY
        path.write_bytes(path.read_bytes() + b"x")
        git(self.root, "add", PLUGIN_COPY)
        git(self.root, "commit", "-q", "--no-verify", "-m", "diverge")  # розбіжність уже в HEAD
        (self.root / "README.md").write_text("r", encoding="utf-8")
        git(self.root, "add", "README.md")  # у цьому коміті копія плагіна не змінюється
        done = self.commit()
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("error shared.differing", done.stdout + done.stderr)

if __name__ == "__main__":
    unittest.main()
