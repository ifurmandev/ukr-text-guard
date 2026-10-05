import contextlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import shared_sync as ss  # noqa: E402


def copy_path(plugin, rel):
    return f"plugins/{plugin}/skills/{plugin}/{rel}"


def make_tree(source, copies):
    """Дерево в памʼяті: source {rel: bytes}, copies {(plugin, rel): bytes}."""
    files = {f"shared/{rel}": data for rel, data in source.items()}
    for (plugin, rel), data in copies.items():
        files[copy_path(plugin, rel)] = data
    return ss.MemoryTree(files)


def codes(plan):
    return sorted((f.code, f.path, f.plugin) for f in plan.findings)


class BuildPlanTest(unittest.TestCase):
    carry = {"a.md": ["p1", "p2"]}

    def tree(self, copies, extra=None):
        t = make_tree({"a.md": b"one\n"}, copies)
        t.files.update(extra or {})
        return t

    def test_all_equal(self):
        t = self.tree({("p1", "a.md"): b"one\n", ("p2", "a.md"): b"one\n"})
        plan = ss.build_plan(t, self.carry)
        self.assertEqual(plan.findings, [])
        self.assertEqual(plan.checked, 2)

    def test_differing(self):
        t = self.tree({("p1", "a.md"): b"two\n", ("p2", "a.md"): b"one\n"})
        plan = ss.build_plan(t, self.carry)
        self.assertEqual(codes(plan), [("shared.differing", "a.md", "p1")])

    def test_missing(self):
        t = self.tree({("p1", "a.md"): b"one\n", ("p2", "x.md"): b"x"})
        plan = ss.build_plan(t, self.carry)
        self.assertEqual(codes(plan), [("shared.missing", "a.md", "p2")])

    def test_unlisted(self):
        carry = {"a.md": ["p1"]}
        t = self.tree({("p1", "a.md"): b"one\n", ("p2", "a.md"): b"one\n"})
        plan = ss.build_plan(t, carry)
        self.assertEqual(codes(plan), [("shared.unlisted", "a.md", "p2")])

    def test_line_endings_only(self):
        t = self.tree({("p1", "a.md"): b"one\r\n", ("p2", "a.md"): b"one\n"})
        plan = ss.build_plan(t, self.carry)
        self.assertEqual(codes(plan), [("shared.line_endings", "a.md", "p1")])

    def test_crlf_and_bytes_differ_is_differing(self):
        t = self.tree({("p1", "a.md"): b"two\r\n", ("p2", "a.md"): b"one\n"})
        plan = ss.build_plan(t, self.carry)
        self.assertEqual(codes(plan), [("shared.differing", "a.md", "p1")])

    def test_invisible_mark_is_differing_with_detail(self):
        mark = "\u200b".encode("utf-8")
        t = self.tree({("p1", "a.md"): b"one" + mark + b"\n", ("p2", "a.md"): b"one\n"})
        plan = ss.build_plan(t, self.carry)
        self.assertEqual(codes(plan), [("shared.differing", "a.md", "p1")])
        self.assertIn("invisible mark", plan.findings[0].detail)

    def test_other_files_in_plugin_are_not_counted(self):
        t = self.tree(
            {("p1", "a.md"): b"one\n", ("p2", "a.md"): b"one\n"},
            {copy_path("p1", "scripts/__pycache__/x.pyc"): b"\x00"},
        )
        self.assertEqual(ss.build_plan(t, self.carry).findings, [])

    def test_orphan_source(self):
        t = make_tree({"a.md": b"one\n", "b.md": b"b"}, {("p1", "a.md"): b"one\n"})
        plan = ss.build_plan(t, {"a.md": ["p1"]})
        self.assertEqual(codes(plan), [("shared.orphan_source", "b.md", "")])

    def test_carry_json_is_not_a_shared_file(self):
        t = self.tree(
            {("p1", "a.md"): b"one\n", ("p2", "a.md"): b"one\n"},
            {"shared/carry.json": b"{}"},
        )
        self.assertEqual(ss.build_plan(t, self.carry).findings, [])

    def test_plan_does_not_write(self):
        t = self.tree({("p1", "a.md"): b"two\n"})
        before = dict(t.files)
        ss.build_plan(t, self.carry)
        self.assertEqual(t.files, before)


class ValidateCarryTest(unittest.TestCase):
    source = ["a.md"]
    plugins = ["p1", "p2"]

    def check(self, carry):
        return [(f.code, f.path, f.plugin) for f in ss.validate_carry(carry, self.source, self.plugins)]

    def test_valid(self):
        self.assertEqual(self.check({"a.md": ["p1", "p2"]}), [])

    def test_key_not_in_source(self):
        self.assertEqual(self.check({"a.md": ["p1"], "zzz.md": ["p1"]}), [("shared.carry_entry", "zzz.md", "")])

    def test_unknown_plugin(self):
        self.assertEqual(self.check({"a.md": ["nope"]}), [("shared.carry_entry", "a.md", "nope")])

    def test_path_leaves_plugin_folder(self):
        for key in ("../x", "a/../../x", "/abs/x", "C:/x", "..\\x"):
            with self.subTest(key=key):
                got = ss.validate_carry({key: ["p1"]}, [key], self.plugins)
                self.assertEqual([f.code for f in got], ["shared.carry_entry"])
                self.assertIn("leaves the plugin folder", got[0].detail)

    def test_plugin_name_with_separator(self):
        got = ss.validate_carry({"a.md": ["../p1"]}, self.source, ["../p1"])
        self.assertEqual([f.code for f in got], ["shared.carry_entry"])

    def test_malformed_shape(self):
        got = ss.validate_carry({"a.md": "p1"}, self.source, self.plugins)
        self.assertEqual([f.code for f in got], ["shared.carry_entry"])

    def test_orphan_source_reported(self):
        got = ss.validate_carry({}, ["a.md"], self.plugins)
        self.assertEqual([(f.code, f.path) for f in got], [("shared.orphan_source", "a.md")])

    def test_wrong_entry_is_not_also_compared(self):
        t = make_tree({"a.md": b"one\n"}, {})
        plan = ss.build_plan(t, {"a.md": ["nope"]})
        self.assertEqual([f.code for f in plan.findings], ["shared.carry_entry"])


REPO = Path(__file__).resolve().parent.parent.parent


def write_tree(root, files):
    for rel, data in files.items():
        path = Path(root) / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


def snapshot(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in Path(root).rglob("*") if p.is_file()}


def run_main(argv, root=None):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = ss.main(argv, root=root)
    return code, out.getvalue(), err.getvalue()


NOTICE = (
    "note: plugin copies are overwritten by the shared source (shared/); "
    "a change made in a copy must be moved to shared/ before running sync"
)


class CheckCommandTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def build(self, copies, carry=None, source=None):
        source = source if source is not None else {"a.md": b"one\n"}
        carry = carry if carry is not None else {"a.md": ["p1", "p2"]}
        files = {f"shared/{k}": v for k, v in source.items()}
        files["shared/carry.json"] = json.dumps(carry).encode("utf-8")
        for (plugin, rel), data in copies.items():
            files[copy_path(plugin, rel)] = data
        write_tree(self.root, files)

    def test_real_repository_passes(self):
        code, out, err = run_main(["check"], root=REPO)
        self.assertEqual(out, "checked 12 files in 3 plugins\nresult: passed\n")
        self.assertEqual((code, err), (0, ""))

    def test_pass_counts_files_and_plugins(self):
        self.build({("p1", "a.md"): b"one\n", ("p2", "a.md"): b"one\n"})
        code, out, _ = run_main(["check"], root=self.root)
        self.assertEqual((code, out), (0, "checked 2 files in 2 plugins\nresult: passed\n"))

    def test_divergence_names_file_plugin_and_notice(self):
        self.build({("p1", "a.md"): b"two\n", ("p2", "a.md"): b"one\n"})
        code, out, _ = run_main(["check"], root=self.root)
        self.assertEqual(code, 3)
        self.assertEqual(
            out.splitlines(),
            ["error shared.differing: a.md p1 copy differs from shared/a.md", NOTICE, "result: failed"],
        )

    def test_missing_prints_notice(self):
        self.build({("p1", "a.md"): b"one\n", ("p2", "x.md"): b"x"})
        code, out, _ = run_main(["check"], root=self.root)
        self.assertEqual(code, 3)
        self.assertIn("error shared.missing: a.md p2 copy is not present", out)
        self.assertIn(NOTICE, out)

    def test_unlisted_only_has_no_notice(self):
        self.build({("p1", "a.md"): b"one\n", ("p2", "a.md"): b"one\n"}, carry={"a.md": ["p1"]})
        code, out, _ = run_main(["check"], root=self.root)
        self.assertEqual(code, 3)
        self.assertIn("error shared.unlisted: a.md p2", out)
        self.assertNotIn(NOTICE, out)
        self.assertEqual(out.splitlines()[-1], "result: failed")

    def test_wrong_carry_entry_fails_and_names_it(self):
        self.build({("p1", "a.md"): b"one\n"}, carry={"a.md": ["p1"], "../x": ["p1"]})
        code, out, _ = run_main(["check"], root=self.root)
        self.assertEqual(code, 3)
        self.assertIn("error shared.carry_entry: ../x", out)

    def test_orphan_source_fails_and_names_it(self):
        self.build({("p1", "a.md"): b"one\n"}, source={"a.md": b"one\n", "b.md": b"b"}, carry={"a.md": ["p1"]})
        code, out, _ = run_main(["check"], root=self.root)
        self.assertEqual(code, 3)
        self.assertIn("error shared.orphan_source: b.md", out)

    def test_check_writes_nothing(self):
        self.build({("p1", "a.md"): b"two\n", ("p2", "x.md"): b"x"}, carry={"a.md": ["p1", "p2"]})
        before = snapshot(self.root)
        run_main(["check"], root=self.root)
        self.assertEqual(snapshot(self.root), before)

    def test_missing_carry_json_is_cannot_run(self):
        write_tree(self.root, {"shared/a.md": b"one\n"})
        code, out, err = run_main(["check"], root=self.root)
        self.assertEqual((code, out), (4, ""))
        self.assertTrue(err.startswith("error shared.cannot_run: "))

    def test_malformed_carry_json_is_cannot_run(self):
        write_tree(self.root, {"shared/carry.json": b"{not json"})
        code, _, err = run_main(["check"], root=self.root)
        self.assertEqual(code, 4)
        self.assertTrue(err.startswith("error shared.cannot_run: "))

    def test_usage_errors_exit_4(self):
        for argv in ([], ["bogus"], ["check", "--nope"], ["sync", "--staged"], ["check", "extra"]):
            with self.subTest(argv=argv):
                code, out, err = run_main(argv, root=self.root)
                self.assertEqual((code, out), (4, ""))
                self.assertTrue(err.startswith("error shared.cannot_run: usage"), err)

    def test_unexpected_exception_exits_4_never_1(self):
        self.build({("p1", "a.md"): b"one\n", ("p2", "a.md"): b"one\n"})
        with mock.patch.object(ss, "build_plan", side_effect=RuntimeError("boom")):
            code, _, err = run_main(["check"], root=self.root)
        self.assertEqual(code, 4)
        self.assertIn("error shared.cannot_run: boom", err)

    def test_unreadable_copy_is_cannot_run_not_divergence(self):
        self.build({("p1", "a.md"): b"one\n", ("p2", "a.md"): b"one\n"})
        real_open = open

        def fake_open(path, *a, **k):
            if str(path).replace("\\", "/").endswith("skills/p1/a.md"):
                raise PermissionError("denied")
            return real_open(path, *a, **k)

        with mock.patch("builtins.open", fake_open):
            code, out, err = run_main(["check"], root=self.root)
        self.assertEqual((code, out), (4, ""))
        self.assertIn("shared.cannot_run", err)


class SyncCommandTest(unittest.TestCase):
    carry = {"a.md": ["p1", "p2"]}

    def sync(self, copies, carry=None, source=None):
        tree = make_tree(source or {"a.md": b"one"}, copies)
        for plugin in ("p1", "p2"):  # плагін існує як папка завжди
            tree.files[copy_path(plugin, "SKILL.md")] = b"s"
        tree.files["shared/carry.json"] = json.dumps(carry or self.carry).encode("utf-8")
        lines, code = ss.sync_command(tree)
        return tree, lines, code

    def test_rewrites_diverged_and_creates_missing(self):
        tree, lines, code = self.sync({("p1", "a.md"): b"old"})
        self.assertEqual(code, 0)
        self.assertEqual(lines, ["rewrote a.md p1", "created a.md p2", "result: passed"])
        for plugin in ("p1", "p2"):
            self.assertEqual(tree.files[copy_path(plugin, "a.md")], b"one")

    def test_writes_only_the_diverged_copies(self):
        tree, _, _ = self.sync({("p1", "a.md"): b"old", ("p2", "a.md"): b"one"})
        self.assertEqual(tree.written, [copy_path("p1", "a.md")])

    def test_second_run_writes_nothing(self):
        tree, _, _ = self.sync({("p1", "a.md"): b"old"})
        tree.written.clear()
        lines, code = ss.sync_command(tree)
        self.assertEqual((lines, code), (["all copies are up to date", "result: passed"], 0))
        self.assertEqual(tree.written, [])

    def test_up_to_date(self):
        tree, lines, code = self.sync({("p1", "a.md"): b"one", ("p2", "a.md"): b"one"})
        self.assertEqual((lines, code), (["all copies are up to date", "result: passed"], 0))
        self.assertEqual(tree.written, [])

    def test_wrong_carry_entry_writes_nothing(self):
        tree, lines, code = self.sync({("p1", "a.md"): b"old"}, carry={"a.md": ["p1"], "../x": ["p1"]})
        self.assertEqual(code, 3)
        self.assertEqual(tree.written, [])
        self.assertTrue(lines[0].startswith("error shared.carry_entry: ../x"))
        self.assertEqual(lines[-1], "result: failed")

    def test_orphan_source_writes_nothing(self):
        tree, lines, code = self.sync(
            {("p1", "a.md"): b"old"}, source={"a.md": b"one", "b.md": b"b"}, carry={"a.md": ["p1"]}
        )
        self.assertEqual((code, tree.written), (3, []))
        self.assertIn("error shared.orphan_source: b.md no plugin carries this shared file", lines)

    def test_unlisted_file_stays_and_sync_fails(self):
        tree, lines, code = self.sync(
            {("p1", "a.md"): b"old", ("p2", "a.md"): b"keep"}, carry={"a.md": ["p1"]}
        )
        self.assertEqual(code, 3)
        self.assertEqual(
            lines,
            [
                "rewrote a.md p1",
                "left in place, delete by hand: a.md p2",
                "error shared.unlisted: a.md p2 the check still fails until this file is deleted",
                "result: failed",
            ],
        )
        self.assertEqual(tree.files[copy_path("p2", "a.md")], b"keep")
        self.assertNotIn("all copies are up to date", lines)

    def test_unlisted_alone_never_says_up_to_date(self):
        _, lines, code = self.sync(
            {("p1", "a.md"): b"one", ("p2", "a.md"): b"one"}, carry={"a.md": ["p1"]}
        )
        self.assertEqual(code, 3)
        self.assertNotIn("all copies are up to date", lines)

    def test_nothing_is_deleted(self):
        extra = {("p1", "other.txt"): b"x", ("p2", "a.md"): b"keep"}
        tree = make_tree({"a.md": b"one"}, {("p1", "a.md"): b"old", **extra})
        tree.files["shared/carry.json"] = json.dumps({"a.md": ["p1"]}).encode("utf-8")
        before = set(tree.files)
        ss.sync_command(tree)
        self.assertTrue(before <= set(tree.files))

    def test_sync_touches_nothing_outside_carried_copies(self):
        tree, _, _ = self.sync({("p1", "a.md"): b"old", ("p1", "keep.txt"): b"k"})
        self.assertEqual(tree.files[copy_path("p1", "keep.txt")], b"k")
        self.assertEqual(
            sorted(tree.written), [copy_path("p1", "a.md"), copy_path("p2", "a.md")]
        )

    def test_hand_edited_copy_is_overwritten_and_listed(self):
        tree, lines, _ = self.sync({("p1", "a.md"): b"hand edit", ("p2", "a.md"): b"one"})
        self.assertEqual(lines[0], "rewrote a.md p1")
        self.assertEqual(tree.files[copy_path("p1", "a.md")], b"one")

    def test_bytes_written_without_line_ending_translation(self):
        crlf = b"one" + bytes([13, 10]) + b"two"
        tree, _, _ = self.sync({}, source={"a.md": crlf}, carry={"a.md": ["p1"]})
        self.assertEqual(tree.files[copy_path("p1", "a.md")], crlf)


class SyncMainTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def test_real_repository_copy_is_up_to_date_and_unchanged(self):
        for top in ("shared", "plugins"):
            shutil.copytree(REPO / top, self.root / top)
        before = snapshot(self.root)
        code, out, err = run_main(["sync"], root=self.root)
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(out.splitlines(), ["all copies are up to date", "result: passed"])
        self.assertEqual(snapshot(self.root), before)

    def test_folder_sync_creates_folders_inside_the_plugin_only(self):
        write_tree(
            self.root,
            {
                "shared/a/b.md": b"one",
                "shared/carry.json": json.dumps({"a/b.md": ["p1"]}).encode("utf-8"),
                "plugins/p1/skills/p1/SKILL.md": b"s",
            },
        )
        code, out, _ = run_main(["sync"], root=self.root)
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines()[0], "created a/b.md p1")
        self.assertEqual((self.root / copy_path("p1", "a/b.md")).read_bytes(), b"one")
        self.assertEqual(
            sorted(snapshot(self.root)),
            sorted([
                "shared/a/b.md", "shared/carry.json",
                "plugins/p1/skills/p1/SKILL.md", copy_path("p1", "a/b.md"),
            ]),
        )

    def test_write_failure_is_cannot_run(self):
        write_tree(
            self.root,
            {
                "shared/a.md": b"one",
                "shared/carry.json": json.dumps({"a.md": ["p1"]}).encode("utf-8"),
                "plugins/p1/skills/p1/SKILL.md": b"s",
            },
        )
        with mock.patch.object(ss.FolderTree, "write", side_effect=PermissionError("denied")):
            code, out, err = run_main(["sync"], root=self.root)
        self.assertEqual((code, out), (4, ""))
        self.assertIn("error shared.cannot_run: denied", err)


def git(root, *args):
    return subprocess.run(
        ["git", "-C", str(root), *args], check=True, capture_output=True
    ).stdout


class StagedCheckTest(unittest.TestCase):
    """Інтеграційні тести на справжньому тимчасовому Git-репозиторії."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        git(self.root, "init", "-q")
        write_tree(
            self.root,
            {
                "shared/a.md": b"one",
                "shared/carry.json": json.dumps({"a.md": ["p1", "p2"]}).encode("utf-8"),
                copy_path("p1", "a.md"): b"one",
                copy_path("p2", "a.md"): b"one",
            },
        )
        git(self.root, "add", "-A")

    def stage(self, rel, data):
        write_tree(self.root, {rel: data})
        git(self.root, "add", rel)

    def test_staged_equal_passes(self):
        code, out, err = run_main(["check", "--staged"], root=self.root)
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(out.splitlines(), ["checked 2 files in 2 plugins", "result: passed"])

    def test_staged_divergence_fails_even_with_working_folder_fixed(self):
        self.stage(copy_path("p1", "a.md"), b"two")
        write_tree(self.root, {copy_path("p1", "a.md"): b"one"})  # робоча папка виправлена
        code, out, _ = run_main(["check", "--staged"], root=self.root)
        self.assertEqual(code, 3)
        self.assertIn("error shared.differing: a.md p1", out)
        self.assertEqual(run_main(["check"], root=self.root)[0], 0)

    def test_staged_equal_passes_even_with_working_folder_diverged(self):
        write_tree(self.root, {copy_path("p1", "a.md"): b"two"})  # лише в робочій папці
        code, out, _ = run_main(["check", "--staged"], root=self.root)
        self.assertEqual((code, out.splitlines()[-1]), (0, "result: passed"))
        self.assertEqual(run_main(["check"], root=self.root)[0], 3)

    def test_staged_shared_source_is_judged_as_staged(self):
        self.stage("shared/a.md", b"newer")
        write_tree(self.root, {"shared/a.md": b"one"})
        code, out, _ = run_main(["check", "--staged"], root=self.root)
        self.assertEqual(code, 3)
        self.assertIn("error shared.differing: a.md p1", out)
        self.assertIn("error shared.differing: a.md p2", out)

    def test_staged_wrong_carry_entry_is_named(self):
        self.stage("shared/carry.json", json.dumps({"a.md": ["p1", "p2"], "../x": ["p1"]}).encode("utf-8"))
        code, out, _ = run_main(["check", "--staged"], root=self.root)
        self.assertEqual(code, 3)
        self.assertIn("error shared.carry_entry: ../x", out)

    def test_untracked_file_is_not_in_the_index(self):
        write_tree(self.root, {copy_path("p3", "a.md"): b"zzz"})  # не додано до індексу
        code, _, _ = run_main(["check", "--staged"], root=self.root)
        self.assertEqual(code, 0)

    def test_path_with_spaces_and_non_ascii_is_kept_intact(self):
        self.stage("shared/carry.json", json.dumps({"a.md": ["p1", "p2"]}).encode("utf-8"))
        self.stage(copy_path("p1", "дані файл.txt"), b"x")
        code, _, _ = run_main(["check", "--staged"], root=self.root)
        self.assertEqual(code, 0)

    def test_check_staged_changes_neither_working_folder_nor_index(self):
        self.stage(copy_path("p1", "a.md"), b"two")
        before_files = snapshot(self.root / "shared"), snapshot(self.root / "plugins")
        before_index = git(self.root, "ls-files", "-s")
        run_main(["check", "--staged"], root=self.root)
        self.assertEqual((snapshot(self.root / "shared"), snapshot(self.root / "plugins")), before_files)
        self.assertEqual(git(self.root, "ls-files", "-s"), before_index)

    def test_not_a_git_repository_is_cannot_run(self):
        with tempfile.TemporaryDirectory() as plain:
            code, out, err = run_main(["check", "--staged"], root=plain)
        self.assertEqual((code, out), (4, ""))
        self.assertTrue(err.startswith("error shared.cannot_run: git index could not be read: "), err)

    def test_git_missing_is_cannot_run(self):
        with mock.patch.object(subprocess, "run", side_effect=FileNotFoundError("git")):
            code, out, err = run_main(["check", "--staged"], root=self.root)
        self.assertEqual((code, out), (4, ""))
        self.assertTrue(err.startswith("error shared.cannot_run: git index could not be read: "), err)


if __name__ == "__main__":
    unittest.main()
