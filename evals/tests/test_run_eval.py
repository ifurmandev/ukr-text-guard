import sys
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


if __name__ == "__main__":
    unittest.main()
