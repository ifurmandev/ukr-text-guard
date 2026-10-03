#!/usr/bin/env python3
"""Перевірка детектора: прогін зразків через аналізатор і порівняння з очікуваними смугами."""
import json
import os
import subprocess
import sys
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


Error = namedtuple("Error", "kind item reason")


def read_known_gaps(path):
    """Читає known-gaps.txt: пари (назва, причина); відсутній файл дає порожній список."""
    path = Path(path)
    if not path.is_file():
        return []
    entries = []
    for line in path.read_bytes().decode("utf-8", errors="replace").splitlines():
        name, _, reason = line.partition("#")
        name = name.strip()
        if name:
            entries.append((name, reason.strip()))
    return entries


def apply_known_gaps(entries, classified):
    """Множина позначених ai-зразків і помилки eval.bad_known_gap (немає такого зразка або він human)."""
    flagged, errors = set(), []
    for name, _reason in entries:
        if name in classified.ai:
            flagged.add(name)
        elif name in classified.human:
            errors.append(Error("eval.bad_known_gap", name, "known-gap cannot be put on a human sample"))
        else:
            errors.append(Error("eval.bad_known_gap", name, "no such sample"))
    return flagged, errors


HIDDEN_CHARS = ("\ufeff", "\u200b", "\u200c", "\u200d", "\u2060")


def _has_hidden_characters(data):
    text = data.decode("utf-8", errors="replace")
    return any(ch in text for ch in HIDDEN_CHARS)


def _last_line(raw):
    lines = [ln for ln in raw.decode("utf-8", errors="replace").splitlines() if ln.strip()]
    return lines[-1].strip() if lines else ""


def _parse_result(stdout):
    """Розбирає JSON аналізатора: Analysis або Failure з причиною."""
    text = stdout.decode("utf-8", errors="replace").strip()
    if not text:
        return Failure("empty result")
    try:
        data = json.loads(text)
    except ValueError:
        return Failure("unreadable result")
    if not isinstance(data, dict):
        return Failure("unreadable result")
    metrics = data.get("метрики")
    index = data.get("індекс")
    reliability = data.get("надійність_статистики")
    words = metrics.get("слів") if isinstance(metrics, dict) else None
    if index is None or reliability is None or words is None:
        return Failure("incomplete result")
    for number in (index, words):
        if isinstance(number, bool) or not isinstance(number, int):
            return Failure("unreadable result")
    if not isinstance(reliability, str):
        return Failure("unreadable result")
    if not reliability.strip():
        return Failure("incomplete result")
    if not 0 <= index <= 100:
        return Failure("index out of range: %d" % index)
    return Analysis(index, words, reliability)


def analyze_sample(analyzer_path, sample_path):
    """Один зразок у свіжому процесі. Повертає (Analysis | Failure, є_приховані_символи)."""
    try:
        data = Path(sample_path).read_bytes()
    except OSError as exc:
        return Failure("unreadable sample file: %s" % exc), False
    hidden = _has_hidden_characters(data)
    env = dict(os.environ, PYTHONUTF8="1")
    try:
        done = subprocess.run(
            [sys.executable, str(analyzer_path), str(sample_path), "--json"],
            env=env, capture_output=True, timeout=SAMPLE_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:
        return Failure("timed out after %s s" % SAMPLE_TIMEOUT_S), hidden
    except OSError as exc:
        return Failure("crashed: could not start the analyzer: %s" % exc), hidden
    if done.returncode != 0:
        detail = _last_line(done.stderr)
        reason = "crashed: exit code %d" % done.returncode
        return Failure(reason + (", " + detail if detail else "")), hidden
    return _parse_result(done.stdout), hidden
