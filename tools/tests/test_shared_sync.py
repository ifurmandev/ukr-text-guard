import contextlib
import io
import json
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


if __name__ == "__main__":
    unittest.main()
