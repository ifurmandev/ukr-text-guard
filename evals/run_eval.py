#!/usr/bin/env python3
"""Перевірка детектора: прогін зразків через аналізатор і порівняння з очікуваними смугами."""
import argparse
import json
import os
import re
import subprocess
import sys
import time
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
        if not item.is_file() or item.suffix.lower() != ".txt":
            ignored.append(item.name)
        elif item.suffix != ".txt":
            unclassified.append(item.name)  # .TXT and the like: reported, never skipped
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
    for line in path.read_bytes().decode("utf-8-sig", errors="replace").splitlines():
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


# Той самий набір невидимих символів, що рахує аналізатор (analyze.py).
HIDDEN_CHARS = re.compile("[\u200b-\u200f\u2060-\u2063\ufeff\u00ad\u034f]")


def _file_quirk(data):
    """"encoding" для не-UTF-8 байтів, "hidden" для невидимих символів, інакше порожній рядок."""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return "encoding"
    return "hidden" if HIDDEN_CHARS.search(text) else ""


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
    """Один зразок у свіжому процесі. Повертає (Analysis | Failure, "" | "hidden" | "encoding")."""
    try:
        data = Path(sample_path).read_bytes()
    except OSError as exc:
        return Failure("unreadable sample file: %s" % exc), ""
    hidden = _file_quirk(data)
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


Row = namedtuple("Row", "name category known_gap outcome verdict hidden")


def _gather(root, analyzer_path):
    """Класифікує теку, застосовує known-gap, аналізує та оцінює кожен зразок за порядком назв."""
    root = Path(root)
    classified = classify_folder(root / "evals" / "samples")
    entries = read_known_gaps(root / "evals" / "known-gaps.txt")
    flagged, gap_errors = apply_known_gaps(entries, classified)
    errors = [Error("eval.unclassified_sample", n, "file name is not human-*.txt or ai-*.txt")
              for n in classified.unclassified]
    errors += gap_errors
    errors += [Error("eval.missing_category", c, "no samples in this category")
               for c in missing_categories(classified)]
    names = sorted([(n, "human") for n in classified.human] + [(n, "ai") for n in classified.ai])
    rows = []
    for name, category in names:
        outcome, hidden = analyze_sample(
            analyzer_path, root / "evals" / "samples" / (name + ".txt"))
        known_gap = name in flagged
        rows.append(Row(name, category, known_gap, outcome,
                        judge(category, known_gap, outcome), hidden))
    return classified, entries, flagged, errors, rows


def _row_line(row):
    label = "known-gap AI" if row.known_gap else ("human" if row.category == "human" else "AI")
    head = "%-40s %-13s" % (row.name, label)
    if isinstance(row.outcome, Failure):
        return "%s analyzer failure: %s   failed" % (head, row.outcome.reason)
    o = row.outcome
    return "%s index %d   words %d   reliability %s   %s" % (
        head, o.index, o.words, o.reliability, "passed" if row.verdict.passed else "failed")


def render_report(plugin, gathered, duration):
    """Збирає звіт у порядку розділів контракту; повертає (текст, failed)."""
    classified, entries, flagged, errors, rows = gathered
    errors = list(errors)
    out = ["plugin: %s" % plugin]
    out += [_row_line(r) for r in rows]

    false_alarms = [r for r in rows if r.verdict.kind == "eval.false_alarm"]
    misses = [r for r in rows if r.verdict.kind == "eval.miss"]
    errors += [Error("eval.analyzer_failure", r.name, r.outcome.reason)
               for r in rows if isinstance(r.outcome, Failure)]
    if false_alarms:
        out.append("")
        out.append("false alarms (human samples above %d):" % HUMAN_MAX)
        out += ["  false alarm: %s index %d" % (r.name, r.outcome.index) for r in false_alarms]
    if misses:
        out.append("")
        out.append("misses (ordinary AI samples below %d):" % AI_MIN)
        out += ["  miss: %s index %d" % (r.name, r.outcome.index) for r in misses]
    if errors:
        out.append("")
        out.append("errors:")
        out += ["  error %s: %s - %s" % (e.kind, e.item, e.reason) for e in errors]
    reasons = dict(entries)
    if flagged:
        out.append("")
        out.append("known-gap samples (excused by evals/known-gaps.txt):")
        for name in sorted(flagged):
            out.append("  known-gap: %s%s" % (name, "  # " + reasons[name] if reasons[name] else ""))

    human_rows = [r for r in rows if r.category == "human"]
    long_human = [r for r in human_rows
                  if isinstance(r.outcome, Analysis) and r.outcome.words >= RELIABLE_WORDS]
    inconclusive = bool(human_rows) and len(long_human) < len(human_rows)
    notes = []
    for r in rows:
        if r.verdict.note == "drift":
            notes.append("drift: %s index %d is above %d, still within the human band of %d"
                         % (r.name, r.outcome.index, HUMAN_DRIFT_ABOVE, HUMAN_MAX))
        elif r.verdict.note == "gap_may_be_closed":
            notes.append("gap may be closed: %s index %d reaches the AI band of %d, review the label"
                         % (r.name, r.outcome.index, AI_MIN))
        if r.hidden == "hidden":
            notes.append("hidden characters: %s has a byte-order mark or invisible characters, "
                         "a high index may come from the file rather than the text" % r.name)
        elif r.hidden == "encoding":
            notes.append("unexpected encoding: %s is not valid UTF-8, "
                         "the index may come from the file rather than the text" % r.name)
    if inconclusive:
        notes.append("human conclusion inconclusive: only %d of %d human samples reach %d words"
                     % (len(long_human), len(human_rows), RELIABLE_WORDS))
    if notes:
        out.append("")
        out.append("notes:")
        out += ["  " + n for n in notes]

    ordinary = [r for r in rows if r.category == "ai" and not r.known_gap
                and isinstance(r.outcome, Analysis)]
    failed = bool(errors) or any(not r.verdict.passed for r in rows)
    out.append("")
    out.append("summary: %d human, %d AI, %d unclassified, %d ignored, %d of %d items"
               % (len(classified.human), len(classified.ai), len(classified.unclassified),
                  len(classified.ignored),
                  len(classified.human) + len(classified.ai) + len(classified.unclassified)
                  + len(classified.ignored), classified.total))
    out.append("ordinary AI samples with index %d or more: %d of %d (for information)"
               % (HIGH_LEVEL, sum(1 for r in ordinary if r.verdict.high_level), len(ordinary)))
    out.append("human samples with %d words or more: %d of %d%s"
               % (RELIABLE_WORDS, len(long_human), len(human_rows),
                  ", human conclusion inconclusive" if inconclusive else ""))
    if classified.ignored:
        out.append("ignored: " + ", ".join(classified.ignored))
    out.append("duration %.1f s" % duration)
    out.append("result: %s" % ("failed" if failed else "passed"))
    return "\n".join(out), failed


def run_check(root, analyzer_path, plugin=DEFAULT_PLUGIN):
    """Весь прогін: повертає (текст звіту, failed)."""
    started = time.monotonic()
    gathered = _gather(root, analyzer_path)
    return render_report(plugin, gathered, time.monotonic() - started)


def resolve_detector(root, plugin):
    """Шлях до analyze.py плагіна або None, якщо копії детектора немає."""
    if not plugin or Path(plugin).name != plugin or plugin in (".", ".."):
        return None
    path = Path(root) / "plugins" / plugin / "skills" / plugin / "scripts" / "analyze.py"
    return path if path.is_file() else None


def _parser():
    parser = argparse.ArgumentParser(
        prog="run_eval.py",
        description="Check the detector against expected bands for every sample.")
    parser.add_argument("--plugin", default=DEFAULT_PLUGIN,
                        help="plugin whose detector copy is measured (default: %(default)s)")
    parser.add_argument("--root", default=None,
                        help="repo root holding plugins/ and evals/ (default: derived from this script)")
    return parser


def _print_utf8():
    stream = sys.stdout
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")


def main(argv):
    """Точка входу: повертає лише 0 (нічого не впало) або 1 (будь-що інше)."""
    try:
        args = _parser().parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code in (0, None) else 1
    try:
        _print_utf8()
        root = Path(args.root) if args.root else Path(__file__).resolve().parent.parent
        analyzer = resolve_detector(root, args.plugin)
        if analyzer is None:
            print("plugin: %s" % args.plugin)
            print("error eval.missing_detector_copy: no detector copy exists for plugin %s"
                  % args.plugin)
            print("result: failed")
            return 1
        report, failed = run_check(root, analyzer, args.plugin)
        print(report)
        return 1 if failed else 0
    except Exception as exc:  # будь-який збій самого раннера не має виглядати як успіх
        try:
            print("error eval.runner_error: runner error: %s: %s" % (type(exc).__name__, exc))
            print("result: failed")
        except Exception:
            pass
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
