import sys
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
