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
        self.assertEqual(c.unclassified, ["Human-x", "notes"])
        self.assertEqual(c.ignored, ["ai-y.png", "human-x.md", "sub"])
        self.assertEqual(c.total, 9)  # the file inside sub/ is not a separate item
        self.assertEqual(
            len(c.human) + len(c.ai) + len(c.unclassified) + len(c.ignored), c.total
        )

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
            "plain": (b"Hello", False),
            "bom": (b"\xef\xbb\xbfHello", True),
            "zero-width": ("Hel\u200blo".encode("utf-8"), True),
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


if __name__ == "__main__":
    unittest.main()
