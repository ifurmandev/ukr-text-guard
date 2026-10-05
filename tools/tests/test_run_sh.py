import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
BASH = shutil.which("bash")
PLUGIN_COPY = "plugins/ukr-text-guard/skills/ukr-text-guard/references/lexicon.md"
STUB_RUNNER = (
    "import os, sys\n"
    "print('RUNNER', sys.argv[1:])\n"
    "sys.exit(int(os.environ.get('STUB_EXIT', '0')))\n"
)


@unittest.skipUnless(BASH, "bash is not available")
class RunShTest(unittest.TestCase):
    """evals/run.sh у тимчасовій копії репозиторію зі заглушкою замість раннера."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        for top in ("shared", "plugins", "tools"):
            shutil.copytree(REPO / top, self.root / top, ignore=shutil.ignore_patterns("__pycache__", "tests"))
        (self.root / "evals").mkdir()
        shutil.copy(REPO / "evals" / "run.sh", self.root / "evals" / "run.sh")
        (self.root / "evals" / "run_eval.py").write_text(STUB_RUNNER, encoding="utf-8")

    def run_sh(self, *args, env=None):
        merged = dict(os.environ, **(env or {}))
        done = subprocess.run(
            [BASH, str(self.root / "evals" / "run.sh"), *args],
            capture_output=True, text=True, env=merged, cwd=str(self.root),
        )
        return done.returncode, done.stdout + done.stderr

    def diverge(self):
        path = self.root / PLUGIN_COPY
        path.write_bytes(path.read_bytes() + b"x")

    def test_clean_repository_reaches_the_runner_with_original_arguments(self):
        code, out = self.run_sh("--plugin", "ukr-text-detector")
        self.assertEqual(code, 0, out)
        self.assertIn("RUNNER ['--plugin', 'ukr-text-detector']", out)

    def test_runner_exit_code_is_returned_unchanged(self):
        code, _ = self.run_sh(env={"STUB_EXIT": "1"})
        self.assertEqual(code, 1)

    def test_divergence_stops_before_any_sample_with_exit_3(self):
        self.diverge()
        code, out = self.run_sh()
        self.assertEqual(code, 3, out)
        self.assertNotIn("RUNNER", out)
        self.assertIn("error shared.differing: references/lexicon.md ukr-text-guard", out)
        self.assertIn("the eval did not run, the cause is a divergence", out)

    def test_arguments_do_not_narrow_the_check(self):
        self.diverge()  # розбіжність у guard, аргумент називає detector
        code, out = self.run_sh("--plugin", "ukr-text-detector")
        self.assertEqual(code, 3, out)
        self.assertNotIn("RUNNER", out)

    def test_check_that_cannot_run_ends_with_exit_4(self):
        (self.root / "shared" / "carry.json").write_text("{not json", encoding="utf-8")
        code, out = self.run_sh()
        self.assertEqual(code, 4, out)
        self.assertNotIn("RUNNER", out)
        self.assertIn("the eval did not run, the check could not run", out)

    def test_no_interpreter_ends_with_exit_4(self):
        stubs = self.root.parent / (self.root.name + "-stubs")
        stubs.mkdir()
        self.addCleanup(shutil.rmtree, str(stubs), True)
        for name in ("python3", "python", "py"):
            (stubs / name).write_text("#!/bin/sh\nexit 1\n", encoding="utf-8", newline="\n")
            os.chmod(stubs / name, 0o755)
        code, out = self.run_sh(env={"PATH": str(stubs) + os.pathsep + os.environ["PATH"]})
        self.assertEqual(code, 4, out)
        self.assertIn("no working Python found", out)


if __name__ == "__main__":
    unittest.main()
