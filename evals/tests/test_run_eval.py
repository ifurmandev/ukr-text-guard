import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import run_eval as ev  # noqa: E402


def analysis(index):
    return ev.Analysis(index=index, words=200, reliability="висока")


class JudgeHumanTest(unittest.TestCase):
    def test_boundaries(self):
        table = [
            (0, True, None, None),
            (15, True, None, None),
            (16, True, None, "drift"),
            (25, True, None, "drift"),
            (26, False, "eval.false_alarm", None),
            (100, False, "eval.false_alarm", None),
        ]
        for index, passed, kind, note in table:
            with self.subTest(index=index):
                v = ev.judge("human", False, analysis(index))
                self.assertEqual((v.passed, v.kind, v.note), (passed, kind, note))
                self.assertFalse(v.high_level)

    def test_flag_never_excuses_a_human(self):
        v = ev.judge("human", True, analysis(40))
        self.assertFalse(v.passed)
        self.assertEqual(v.kind, "eval.false_alarm")


class JudgeAiTest(unittest.TestCase):
    def test_boundaries(self):
        table = [
            (0, False, "eval.miss", False),
            (25, False, "eval.miss", False),
            (26, True, None, False),
            (50, True, None, False),
            (51, True, None, True),
            (100, True, None, True),
        ]
        for index, passed, kind, high in table:
            with self.subTest(index=index):
                v = ev.judge("ai", False, analysis(index))
                self.assertEqual((v.passed, v.kind, v.high_level), (passed, kind, high))
                self.assertIsNone(v.note)


class JudgeKnownGapTest(unittest.TestCase):
    def test_low_index_passes_as_known_gap(self):
        v = ev.judge("ai", True, analysis(9))
        self.assertTrue(v.passed)
        self.assertIsNone(v.kind)
        self.assertEqual(v.note, "known_gap")

    def test_reaching_ai_band_warns_never_fails(self):
        for index in (26, 60, 100):
            with self.subTest(index=index):
                v = ev.judge("ai", True, analysis(index))
                self.assertTrue(v.passed)
                self.assertEqual(v.note, "gap_may_be_closed")

    def test_high_level_is_not_counted_for_known_gap(self):
        self.assertFalse(ev.judge("ai", True, analysis(80)).high_level)


class JudgeFailureTest(unittest.TestCase):
    def test_failure_fails_for_every_kind_of_sample(self):
        failure = ev.Failure("timed out")
        for category, flag in (("human", False), ("ai", False), ("ai", True)):
            with self.subTest(category=category, flag=flag):
                v = ev.judge(category, flag, failure)
                self.assertFalse(v.passed)
                self.assertEqual(v.kind, "eval.analyzer_failure")


class ConstantsTest(unittest.TestCase):
    def test_bands(self):
        self.assertEqual(
            (ev.HUMAN_MAX, ev.HUMAN_DRIFT_ABOVE, ev.AI_MIN, ev.HIGH_LEVEL,
             ev.RELIABLE_WORDS, ev.SAMPLE_TIMEOUT_S, ev.DEFAULT_PLUGIN),
            (25, 15, 26, 51, 150, 10, "ukr-text-guard"),
        )

class ClassifyFolderTest(unittest.TestCase):
    def make(self, files=(), dirs=()):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        for name in files:
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("x", encoding="utf-8")
        for name in dirs:
            (root / name).mkdir(parents=True, exist_ok=True)
        return root

    def test_every_kind_of_item(self):
        root = self.make(
            files=["human-b.txt", "human-a.txt", "ai-z.txt", "ai-y.txt", "notes.txt",
                   "Human-x.txt", "human-x.md", "ai-y.png", "sub/ai-inner.txt"],
        )
        c = ev.classify_folder(root)
        self.assertEqual(c.human, ["human-a", "human-b"])
        self.assertEqual(c.ai, ["ai-y", "ai-z"])
        self.assertEqual(c.unclassified, ["Human-x.txt", "notes.txt"])
        self.assertEqual(c.ignored, ["ai-y.png", "human-x.md", "sub"])
        self.assertEqual(c.total, 9)  # the file inside sub/ is not a separate item
        self.assertEqual(
            len(c.human) + len(c.ai) + len(c.unclassified) + len(c.ignored), c.total
        )

    def test_extension_in_any_letter_case_is_judged_by_prefix(self):
        root = self.make(files=["human-a.txt", "ai-b.txt", "human-x.TXT", "ai-y.Txt", "notes.TXT"])
        c = ev.classify_folder(root)
        self.assertEqual(c.human, ["human-a", "human-x"])
        self.assertEqual(c.ai, ["ai-b", "ai-y"])
        self.assertEqual(c.unclassified, ["notes.TXT"])
        self.assertEqual(c.ignored, [])
        self.assertEqual(c.files["human-x"], "human-x.TXT")
        self.assertEqual(c.files["ai-b"], "ai-b.txt")

    def test_same_name_in_two_letter_cases_is_a_collision(self):
        class Item:  # real files differing only in case cannot coexist on NTFS
            def __init__(self, name):
                self.name, self.stem, self.suffix = name, name[:-4], name[-4:]

            def is_file(self):
                return True

        root = self.make()
        items = [Item("human-x.TXT"), Item("human-x.txt"), Item("ai-b.txt")]
        with mock.patch.object(ev.Path, "iterdir", return_value=items):
            c = ev.classify_folder(root)
        self.assertEqual(c.human, ["human-x"])
        self.assertEqual(c.files["human-x"], "human-x.TXT")
        self.assertEqual(c.unclassified, ["human-x.txt"])
        self.assertEqual(c.duplicates, {"human-x.txt": "human-x.TXT"})

    def test_empty_and_missing_folder(self):
        root = self.make()
        for folder in (root, root / "nope"):
            with self.subTest(folder=folder.name):
                c = ev.classify_folder(folder)
                self.assertEqual(c.total, 0)
                self.assertEqual(ev.missing_categories(c), ["samples"])

    def test_missing_categories(self):
        only_human = ev.classify_folder(self.make(files=["human-a.txt"]))
        self.assertEqual(ev.missing_categories(only_human), ["ai"])
        only_ai = ev.classify_folder(self.make(files=["ai-a.txt"]))
        self.assertEqual(ev.missing_categories(only_ai), ["human"])
        both = ev.classify_folder(self.make(files=["ai-a.txt", "human-a.txt"]))
        self.assertEqual(ev.missing_categories(both), [])


class KnownGapTest(unittest.TestCase):
    def classified(self):
        return ev.Classified(["human-a"], ["ai-b", "ai-c"], [], [], 3)

    def write(self, text):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "known-gaps.txt"
        path.write_bytes(text.encode("utf-8"))
        return path

    def test_file_format(self):
        path = self.write("# header\n\nai-b  # imitates human\r\nai-c   \n  \n")
        self.assertEqual(
            ev.read_known_gaps(path), [("ai-b", "imitates human"), ("ai-c", "")]
        )

    def test_leading_bom_is_ignored(self):
        path = self.write("﻿ai-b  # why\n")
        self.assertEqual(ev.read_known_gaps(path), [("ai-b", "why")])

    def test_missing_file_is_empty_list(self):
        self.assertEqual(ev.read_known_gaps(Path("no/such/known-gaps.txt")), [])

    def test_flag_on_ai_sample(self):
        flagged, errors = ev.apply_known_gaps([("ai-b", "why")], self.classified())
        self.assertEqual(flagged, {"ai-b"})
        self.assertEqual(errors, [])

    def test_flag_on_human_sample_is_error_and_no_flag(self):
        flagged, errors = ev.apply_known_gaps([("human-a", "")], self.classified())
        self.assertEqual(flagged, set())
        self.assertEqual([(e.kind, e.item) for e in errors],
                         [("eval.bad_known_gap", "human-a")])

    def test_flag_on_missing_sample_is_error(self):
        flagged, errors = ev.apply_known_gaps([("ai-zzz", "")], self.classified())
        self.assertEqual(flagged, set())
        self.assertEqual([(e.kind, e.item) for e in errors],
                         [("eval.bad_known_gap", "ai-zzz")])

    def test_duplicate_gives_one_flag_no_error(self):
        flagged, errors = ev.apply_known_gaps(
            [("ai-b", ""), ("ai-b", "again")], self.classified())
        self.assertEqual(flagged, {"ai-b"})
        self.assertEqual(errors, [])

    def test_seeded_list_in_repo(self):
        repo = Path(__file__).resolve().parent.parent.parent
        entries = ev.read_known_gaps(repo / "evals" / "known-gaps.txt")
        self.assertEqual([n for n, _ in entries], ["ai-prompted-human-style"])
        self.assertTrue((repo / "evals" / "samples" / "ai-prompted-human-style.txt").exists())

FAKE_HEADER = """import json, sys, time
path = sys.argv[1]


def ok(index=10, words=100, reliability="low"):
    print(json.dumps({"індекс": index, "надійність_статистики": reliability,
                      "метрики": {"слів": words}}))


"""


class AnalyzeSampleTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        self.sample = self.dir / "human-x.txt"
        self.sample.write_text("Привіт, світе.", encoding="utf-8")
        self.analyzer = self.dir / "analyze.py"

    def run_fake(self, body):
        self.analyzer.write_text(FAKE_HEADER + body + "\n", encoding="utf-8")
        return ev.analyze_sample(self.analyzer, self.sample)

    def assert_failure(self, body, reason):
        outcome, _hidden = self.run_fake(body)
        self.assertIsInstance(outcome, ev.Failure)
        self.assertIn(reason, outcome.reason)

    def test_usable_result(self):
        outcome, hidden = self.run_fake('ok(index=37, words=212, reliability="high")')
        self.assertEqual(outcome, ev.Analysis(37, 212, "high"))
        self.assertFalse(hidden)

    def test_index_bounds_accepted(self):
        for index in (0, 100):
            with self.subTest(index=index):
                outcome, _ = self.run_fake("ok(index=%d)" % index)
                self.assertEqual(outcome.index, index)

    def test_index_out_of_range(self):
        for index in (101, -1):
            with self.subTest(index=index):
                self.assert_failure("ok(index=%d)" % index, "index out of range")

    def test_crash_names_exit_code_and_last_stderr_line(self):
        outcome, _ = self.run_fake('sys.stderr.write("first\\nlast line\\n"); sys.exit(3)')
        self.assertIsInstance(outcome, ev.Failure)
        self.assertIn("crashed", outcome.reason)
        self.assertIn("3", outcome.reason)
        self.assertIn("last line", outcome.reason)

    def test_timeout(self):
        with mock.patch.object(ev, "SAMPLE_TIMEOUT_S", 1):
            self.assert_failure("time.sleep(30)", "timed out")

    def test_empty_output(self):
        self.assert_failure("pass", "empty result")

    def test_not_json(self):
        self.assert_failure('print("not json")', "unreadable result")

    def test_json_but_not_an_object(self):
        self.assert_failure("print([1, 2])", "unreadable result")

    def test_missing_keys(self):
        self.assert_failure("print({})", "incomplete result")
        self.assert_failure('print(json.dumps({"індекс": 5}))', "incomplete result")

    def test_values_of_wrong_type_are_not_coerced(self):
        for value in ('"12"', "True", "12.5"):
            with self.subTest(index=value):
                self.assert_failure("ok(index=%s)" % value, "unreadable result")

    def test_empty_reliability(self):
        self.assert_failure('ok(reliability="")', "incomplete result")

    def test_two_calls_are_equal(self):
        self.run_fake("ok(index=44)")
        self.assertEqual(ev.analyze_sample(self.analyzer, self.sample),
                         ev.analyze_sample(self.analyzer, self.sample))

    def test_hidden_characters_flag(self):
        cases = {
            "plain": (b"Hello", ""),
            "bom": (b"\xef\xbb\xbfHello", "hidden"),
            "zero-width": ("Hel\u200blo".encode("utf-8"), "hidden"),
            "soft-hyphen": ("Hel\u00adlo".encode("utf-8"), "hidden"),
            "direction-mark": ("Hel\u200flo".encode("utf-8"), "hidden"),
            "invisible-operator": ("Hel\u2062lo".encode("utf-8"), "hidden"),
            "invalid-utf8": (b"Hel\xff\xfelo", "encoding"),
        }
        for name, (data, expected) in cases.items():
            with self.subTest(name=name):
                self.sample.write_bytes(data)
                outcome, hidden = self.run_fake("ok()")
                self.assertIsInstance(outcome, ev.Analysis)
                self.assertEqual(hidden, expected)

    def test_unreadable_sample_file_is_a_failure(self):
        self.run_fake("ok()")
        outcome, hidden = ev.analyze_sample(self.analyzer, self.dir / "gone.txt")
        self.assertIsInstance(outcome, ev.Failure)
        self.assertFalse(hidden)


FAKE_BY_NAME = '''import json, os, sys
DATA = %r
spec = DATA[os.path.basename(sys.argv[1])[:-4]]
if spec == "crash":
    sys.exit(3)
index, words = spec
print(json.dumps({"індекс": index,
                  "надійність_статистики": "висока" if words >= 150 else "низька",
                  "метрики": {"слів": words}}))
'''


class RunCheckTest(unittest.TestCase):
    """The use case, run against a fake analyzer in a temporary repo root."""

    def build(self, samples, gaps=None, extra_files=(), extra_dirs=()):
        """samples: {file name without .txt: (index, words) | "crash" | (index, words, raw bytes)}"""
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        folder = root / "evals" / "samples"
        folder.mkdir(parents=True)
        data = {}
        for name, spec in samples.items():
            raw = spec[2] if isinstance(spec, tuple) and len(spec) == 3 else b"text"
            (folder / (name + ".txt")).write_bytes(raw)
            data[name] = spec[:2] if isinstance(spec, tuple) else spec
        for name in extra_files:
            (folder / name).write_bytes(b"x")
        for name in extra_dirs:
            (folder / name).mkdir()
        if gaps is not None:
            (root / "evals" / "known-gaps.txt").write_text(gaps, encoding="utf-8")
        analyzer = root / "analyze.py"
        analyzer.write_text(FAKE_BY_NAME % (data,), encoding="utf-8")
        return root, analyzer

    def run_check(self, samples, **kw):
        root, analyzer = self.build(samples, **kw)
        return ev.run_check(root, analyzer, "ukr-text-guard")

    def line_with(self, report, *parts):
        for line in report.splitlines():
            if all(p in line for p in parts):
                return line
        self.fail("no line with %r in:\n%s" % (parts, report))

    def test_all_pass_lists_every_fact(self):
        report, failed = self.run_check({
            "human-a": (5, 200), "ai-b": (60, 300), "ai-c": (30, 120)})
        self.assertFalse(failed)
        self.assertIn("plugin: ukr-text-guard", report)
        line = self.line_with(report, "human-a")
        for fact in ("human", "5", "200", "висока", "passed"):
            self.assertIn(fact, line)
        line = self.line_with(report, "ai-b")
        for fact in ("AI", "60", "300", "passed"):
            self.assertIn(fact, line)
        self.assertIn("result: passed", report)
        self.assertIn("duration", report)

    def test_high_level_count_is_informational(self):
        report, failed = self.run_check({
            "human-a": (5, 200), "ai-b": (60, 300), "ai-c": (30, 300), "ai-d": (51, 300)})
        self.assertFalse(failed)
        self.line_with(report, "ordinary AI", "51", "2 of 3")

    def test_false_alarm_is_listed_and_fails(self):
        report, failed = self.run_check({"human-a": (30, 200), "ai-b": (60, 300)})
        self.assertTrue(failed)
        self.line_with(report, "false alarm", "human-a", "30")
        self.assertIn("result: failed", report)

    def test_miss_is_listed_and_fails(self):
        report, failed = self.run_check({"human-a": (5, 200), "ai-b": (10, 300)})
        self.assertTrue(failed)
        self.line_with(report, "miss", "ai-b", "10")

    def test_notes_alone_never_fail(self):
        report, failed = self.run_check({
            "human-a": (20, 40),            # drift and inconclusive
            "ai-b": (9, 300),               # known-gap, below the band
            "ai-c": (40, 300)},             # known-gap, reaches the band
            gaps="ai-b  # imitates\nai-c  # maybe closed\n")
        self.assertFalse(failed)
        self.line_with(report, "drift", "human-a")
        self.line_with(report, "gap may be closed", "ai-c")
        self.line_with(report, "inconclusive")
        self.assertIn("result: passed", report)

    def test_inconclusive_names_the_counts(self):
        report, _ = self.run_check({
            "human-a": (5, 200), "human-b": (5, 40), "ai-c": (60, 300)})
        self.line_with(report, "150", "1 of 2", "inconclusive")

    def test_conclusive_when_all_human_samples_are_long(self):
        report, failed = self.run_check({"human-a": (5, 200), "ai-b": (60, 300)})
        self.line_with(report, "150", "1 of 1")
        self.assertNotIn("inconclusive", report)
        self.assertFalse(failed)

    def test_known_gap_list_shows_every_excused_sample(self):
        report, _ = self.run_check({
            "human-a": (5, 200), "ai-b": (9, 300), "ai-c": (60, 300)},
            gaps="ai-b  # imitates human writing\n")
        self.line_with(report, "known-gap", "ai-b", "imitates human writing")
        self.line_with(report, "ai-b", "known-gap AI")

    def test_flag_never_excuses_a_sample_without_an_entry(self):
        report, failed = self.run_check({"human-a": (5, 200), "ai-b": (9, 300)})
        self.assertTrue(failed)
        self.line_with(report, "miss", "ai-b")

    def test_analyzer_failure_shows_reason_not_an_index(self):
        report, failed = self.run_check({
            "human-a": "crash", "ai-b": (60, 300)})
        self.assertTrue(failed)
        line = self.line_with(report, "human-a", "crashed")
        self.assertNotIn("index", line)
        self.line_with(report, "eval.analyzer_failure", "human-a")

    def test_bad_known_gap_entry_fails(self):
        report, failed = self.run_check(
            {"human-a": (5, 200), "ai-b": (60, 300)}, gaps="human-a\nai-zzz\n")
        self.assertTrue(failed)
        self.line_with(report, "eval.bad_known_gap", "human-a")
        self.line_with(report, "eval.bad_known_gap", "ai-zzz")

    def test_unclassified_and_ignored_items_are_counted(self):
        report, failed = self.run_check(
            {"human-a": (5, 200), "ai-b": (60, 300), "notes": (1, 1)},
            extra_files=["readme.md"], extra_dirs=["sub"])
        self.assertTrue(failed)
        self.line_with(report, "eval.unclassified_sample", "notes")
        self.line_with(report, "summary", "1 human", "1 AI", "1 unclassified",
                       "2 ignored", "5 of 5")

    def test_upper_case_extension_sample_is_judged_not_skipped(self):
        root, analyzer = self.build({"human-a": (40, 200), "ai-b": (60, 300)})
        folder = root / "evals" / "samples"
        (folder / "human-a.txt").rename(folder / "human-a.TXT")
        report, failed = ev.run_check(root, analyzer, "ukr-text-guard")
        self.assertTrue(failed)
        self.line_with(report, "false alarm", "human-a")
        self.assertNotIn("ignored:", report)

    def test_gather_hands_the_real_file_name_to_the_analyzer(self):
        root, analyzer = self.build({"human-a": (5, 200), "ai-b": (60, 300)})
        folder = root / "evals" / "samples"
        (folder / "human-a.txt").rename(folder / "human-a.TXT")
        seen = []
        real = ev.analyze_sample

        def spy(analyzer_path, sample_path):
            seen.append(Path(sample_path).name)
            return real(analyzer_path, sample_path)

        with mock.patch.object(ev, "analyze_sample", side_effect=spy):
            ev._gather(root, analyzer)
        self.assertEqual(sorted(seen), ["ai-b.txt", "human-a.TXT"])

    def test_collision_is_reported_with_its_own_reason(self):
        root, analyzer = self.build({"human-a": (5, 200), "ai-b": (60, 300)})
        classified = ev.Classified(
            ["human-a"], ["ai-b"], ["human-a.txt"], [], 3,
            {"human-a": "human-a.TXT", "ai-b": "ai-b.txt"}, {"human-a.txt": "human-a.TXT"})
        with mock.patch.object(ev, "classify_folder", return_value=classified):
            with mock.patch.object(ev, "analyze_sample",
                                   return_value=(ev.Analysis(5, 200, "x"), "")):
                errors = ev._gather(root, analyzer)[3]
        reasons = [e.reason for e in errors if e.kind == "eval.unclassified_sample"]
        self.assertEqual(len(reasons), 1)
        self.assertIn("same sample name as human-a.TXT in another letter case", reasons[0])

    def test_ignored_items_do_not_change_a_passing_run(self):
        report, failed = self.run_check(
            {"human-a": (5, 200), "ai-b": (60, 300)},
            extra_files=["readme.md"], extra_dirs=["sub"])
        self.assertFalse(failed)
        self.assertIn("result: passed", report)
        self.line_with(report, "ignored:", "readme.md", "sub")

    def test_missing_category_fails(self):
        report, failed = self.run_check({"ai-b": (60, 300)})
        self.assertTrue(failed)
        self.line_with(report, "eval.missing_category", "human")

    def test_hidden_characters_note(self):
        report, failed = self.run_check({
            "human-a": (5, 200, b"\xef\xbb\xbfhello"), "ai-b": (60, 300)})
        self.assertFalse(failed)
        self.line_with(report, "hidden", "human-a", "file")

    def test_soft_hyphen_note_explains_a_false_alarm(self):
        report, failed = self.run_check({
            "human-a": (32, 200, "Hel­lo".encode("utf-8")), "ai-b": (60, 300)})
        self.assertTrue(failed)
        self.line_with(report, "false alarm", "human-a")
        self.line_with(report, "hidden characters", "human-a")

    def test_invalid_utf8_gets_an_encoding_note(self):
        report, failed = self.run_check({
            "human-a": (5, 200, b"Hel\xff\xfelo"), "ai-b": (60, 300)})
        self.assertFalse(failed)
        self.line_with(report, "unexpected encoding", "human-a")

    def test_two_reports_differ_only_in_the_duration_line(self):
        samples = {"human-a": (20, 40), "ai-b": (9, 300), "ai-c": (60, 300)}
        root, analyzer = self.build(samples, gaps="ai-b\n")
        first, _ = ev.run_check(root, analyzer, "ukr-text-guard")
        second, _ = ev.run_check(root, analyzer, "ukr-text-guard")

        def stripped(text):
            return [ln for ln in text.splitlines() if not ln.startswith("duration")]
        self.assertEqual(stripped(first), stripped(second))

    def test_samples_are_listed_in_sorted_order(self):
        report, _ = self.run_check({
            "human-b": (5, 200), "ai-z": (60, 300), "human-a": (5, 200), "ai-y": (60, 300)})
        positions = [report.index(n) for n in ("ai-y", "ai-z", "human-a", "human-b")]
        self.assertEqual(positions, sorted(positions))


class CliTest(unittest.TestCase):
    def build(self, plugins=("ukr-text-guard",), samples=None):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        samples = samples or {"human-a": (5, 200), "ai-b": (60, 300)}
        folder = root / "evals" / "samples"
        folder.mkdir(parents=True)
        for name in samples:
            (folder / (name + ".txt")).write_bytes(b"text")
        for plugin in plugins:
            scripts = root / "plugins" / plugin / "skills" / plugin / "scripts"
            scripts.mkdir(parents=True)
            (scripts / "analyze.py").write_text(FAKE_BY_NAME % (samples,), encoding="utf-8")
        return root

    def main(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = ev.main(list(argv))
        return code, out.getvalue()

    def test_default_plugin_is_named_and_exit_0(self):
        code, out = self.main("--root", str(self.build()))
        self.assertEqual(code, 0)
        self.assertIn("plugin: ukr-text-guard", out)
        self.assertIn("result: passed", out)

    def test_plugin_option_picks_another_copy(self):
        root = self.build(plugins=("ukr-text-guard", "ukr-text-editor"))
        code, out = self.main("--root", str(root), "--plugin", "ukr-text-editor")
        self.assertEqual(code, 0)
        self.assertIn("plugin: ukr-text-editor", out)

    def test_failing_copy_fails_only_its_own_run(self):
        root = self.build(plugins=("ukr-text-guard",))
        broken = root / "plugins" / "ukr-text-detector" / "skills" / "ukr-text-detector" / "scripts"
        broken.mkdir(parents=True)
        (broken / "analyze.py").write_text("import sys\nsys.exit(2)\n", encoding="utf-8")
        self.assertEqual(self.main("--root", str(root))[0], 0)
        self.assertEqual(self.main("--root", str(root), "--plugin", "ukr-text-detector")[0], 1)

    def test_missing_copy_exits_1_and_says_so(self):
        code, out = self.main("--root", str(self.build()), "--plugin", "ukr-text-unknown")
        self.assertEqual(code, 1)
        self.assertIn("plugin: ukr-text-unknown", out)
        self.assertIn("eval.missing_detector_copy", out)
        self.assertIn("result: failed", out)

    def test_plugin_name_cannot_escape_the_plugins_folder(self):
        code, out = self.main("--root", str(self.build()), "--plugin", "../x")
        self.assertEqual(code, 1)
        self.assertIn("eval.missing_detector_copy", out)

    def test_root_without_plugins_is_a_missing_copy(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        code, out = self.main("--root", tmp.name)
        self.assertEqual(code, 1)
        self.assertIn("eval.missing_detector_copy", out)

    def test_bad_option_exits_1_not_2(self):
        self.assertEqual(self.main("--bogus")[0], 1)
        self.assertEqual(self.main("--plugin")[0], 1)

    def test_help_exits_0(self):
        code, out = self.main("--help")
        self.assertEqual(code, 0)
        self.assertIn("--plugin", out)

    def test_failing_run_exits_1(self):
        root = self.build(samples={"human-a": (40, 200), "ai-b": (60, 300)})
        self.assertEqual(self.main("--root", str(root))[0], 1)

    def test_forced_exception_is_a_runner_error_and_exit_1(self):
        with mock.patch.object(ev, "run_check", side_effect=RuntimeError("boom")):
            code, out = self.main("--root", str(self.build()))
        self.assertEqual(code, 1)
        self.assertIn("error eval.runner_error", out)
        self.assertIn("runner error", out)
        self.assertIn("boom", out)
        self.assertIn("result: failed", out)

    def test_only_0_and_1_are_ever_returned(self):
        root = self.build()
        for argv in ([], ["--plugin", "x"], ["--bogus"], ["--help"]):
            with self.subTest(argv=argv):
                code, _ = self.main("--root", str(root), *argv)
                self.assertIn(code, (0, 1))


REPO = Path(__file__).resolve().parent.parent.parent
REAL_ANALYZER = ev.resolve_detector(REPO, ev.DEFAULT_PLUGIN)


def verdict_of(category, analyze, analyzer, sample):
    outcome, _hidden = analyze(analyzer, sample)
    return outcome, ev.judge(category, False, outcome)


def compare_orders(analyze, analyzer, samples):
    """Verdicts of every sample in sorted order, in reverse order and in a repeated sorted pass.

    Each analysis is a fresh call, so a sample that depends on earlier runs gives a different
    result in at least one pass. Returns the names whose results differ between the passes.
    """
    category = lambda p: "human" if p.stem.startswith("human-") else "ai"  # noqa: E731
    passes = [
        {p.stem: verdict_of(category(p), analyze, analyzer, p) for p in order}
        for order in (samples, list(reversed(samples)), samples)
    ]
    first = passes[0]
    return [name for name in first if not all(other[name] == first[name] for other in passes)]


def compare_alone_to_joint(gather, joint_root, analyzer, samples):
    """Result of each sample run alone (a folder holding only it) against its row in the joint run.

    Returns the names whose (outcome, verdict) differ.
    """
    def rows(root):
        return {r.name: (r.outcome, r.verdict) for r in gather(root, analyzer)[-1]}

    joint = rows(joint_root)
    differing = []
    for sample in samples:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "evals" / "samples"
            folder.mkdir(parents=True)
            (folder / sample.name).write_bytes(sample.read_bytes())
            gaps = joint_root / "evals" / "known-gaps.txt"
            if gaps.is_file():
                (Path(tmp) / "evals" / "known-gaps.txt").write_bytes(gaps.read_bytes())
            if rows(Path(tmp)).get(sample.stem) != joint.get(sample.stem):
                differing.append(sample.stem)
    return differing


class OrderComparisonSelfTest(unittest.TestCase):
    """The comparison must be able to fail, or the real-analyzer test below proves nothing."""

    def test_detects_a_sample_whose_result_depends_on_earlier_runs(self):
        calls = {"n": 0}

        def stateful(_analyzer, _sample):
            calls["n"] += 1
            return ev.Analysis(calls["n"], 100, "x"), False

        samples = [Path("human-a.txt"), Path("ai-b.txt")]
        self.assertEqual(sorted(compare_orders(stateful, None, samples)),
                         ["ai-b", "human-a"])

    def test_alone_comparison_detects_a_result_that_depends_on_other_samples(self):
        def crowd_aware(root, _analyzer):
            count = len(list((Path(root) / "evals" / "samples").glob("*.txt")))
            row = ev.Row("human-a", "human", False, ev.Analysis(count, 100, "x"),
                         ev.Verdict(True, None, None, False), "")
            return (None, [], set(), [], [row])

        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "evals" / "samples"
            folder.mkdir(parents=True)
            samples = []
            for name in ("human-a.txt", "ai-b.txt"):
                (folder / name).write_text("x", encoding="utf-8")
                samples.append(folder / name)
            self.assertEqual(
                compare_alone_to_joint(crowd_aware, Path(tmp), None, samples[:1]), ["human-a"])

    def test_stable_analyzer_gives_no_difference(self):
        def stable(_analyzer, sample):
            return ev.Analysis(len(sample.stem), 100, "x"), False

        self.assertEqual(
            compare_orders(stable, None, [Path("human-a.txt"), Path("ai-b.txt")]), [])


@unittest.skipIf(REAL_ANALYZER is None, "real detector copy ukr-text-guard is absent in this checkout")
class RealAnalyzerTest(unittest.TestCase):
    def test_every_real_sample_gets_the_same_result_in_any_order(self):
        samples = sorted((REPO / "evals" / "samples").glob("*.txt"))
        self.assertTrue(samples, "no real samples found")
        differing = compare_orders(ev.analyze_sample, REAL_ANALYZER, samples)
        self.assertEqual(differing, [], "results differ between runs for: %s" % differing)

    def test_every_real_sample_alone_matches_its_row_in_the_joint_run(self):
        samples = sorted((REPO / "evals" / "samples").glob("*.txt"))
        differing = compare_alone_to_joint(ev._gather, REPO, REAL_ANALYZER, samples)
        self.assertEqual(differing, [], "alone differs from joint for: %s" % differing)

    def test_two_real_reports_differ_only_in_the_duration_line(self):
        def stripped():
            report, _ = ev.run_check(REPO, REAL_ANALYZER, ev.DEFAULT_PLUGIN)
            return [ln for ln in report.splitlines() if not ln.startswith("duration")]

        self.assertEqual(stripped(), stripped())


if __name__ == "__main__":
    unittest.main()
