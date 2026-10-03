#!/usr/bin/env python3
"""Перевірка детектора: прогін зразків через аналізатор і порівняння з очікуваними смугами."""
from collections import namedtuple
from pathlib import Path

# Смуги й ліміти. Єдине місце, де вони записані.
HUMAN_MAX = 25
HUMAN_DRIFT_ABOVE = 15
AI_MIN = 26
HIGH_LEVEL = 51
RELIABLE_WORDS = 150
SAMPLE_TIMEOUT_S = 10
DEFAULT_PLUGIN = "ukr-text-guard"

Analysis = namedtuple("Analysis", "index words reliability")
Failure = namedtuple("Failure", "reason")
Verdict = namedtuple("Verdict", "passed kind note high_level")


def judge(category, known_gap, outcome):
    """Чиста функція: категорія, прапор known-gap і результат аналізу дають вердикт."""
    if isinstance(outcome, Failure):
        return Verdict(False, "eval.analyzer_failure", None, False)
    index = outcome.index
    if category == "human":
        if index > HUMAN_MAX:
            return Verdict(False, "eval.false_alarm", None, False)
        note = "drift" if index > HUMAN_DRIFT_ABOVE else None
        return Verdict(True, None, note, False)
    if known_gap:
        note = "gap_may_be_closed" if index >= AI_MIN else "known_gap"
        return Verdict(True, None, note, False)
    if index < AI_MIN:
        return Verdict(False, "eval.miss", None, False)
    return Verdict(True, None, None, index >= HIGH_LEVEL)


Classified = namedtuple("Classified", "human ai unclassified ignored total")


def classify_folder(samples_dir):
    """Розкладає елементи теки на human, ai, unclassified та ignored; усе відсортовано за назвою."""
    human, ai, unclassified, ignored = [], [], [], []
    samples_dir = Path(samples_dir)
    items = sorted(samples_dir.iterdir(), key=lambda p: p.name) if samples_dir.is_dir() else []
    for item in items:
        if not item.is_file() or item.suffix != ".txt":
            ignored.append(item.name)
        elif item.stem.startswith("human-"):
            human.append(item.stem)
        elif item.stem.startswith("ai-"):
            ai.append(item.stem)
        else:
            unclassified.append(item.stem)
    return Classified(human, ai, unclassified, ignored, len(items))


def missing_categories(classified):
    """Назви відсутніх категорій; "samples", якщо немає жодного зразка."""
    if not classified.human and not classified.ai:
        return ["samples"]
    missing = []
    if not classified.human:
        missing.append("human")
    if not classified.ai:
        missing.append("ai")
    return missing
