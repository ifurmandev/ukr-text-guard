import sys
import tempfile
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
