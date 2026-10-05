#!/usr/bin/env python3
"""Синхронізація спільних файлів: shared/ є єдиним джерелом, копії в плагінах
порівнюються побайтово. Лише стандартна бібліотека, Python 3.8+."""
import json
import os
import sys
from dataclasses import dataclass, field
from typing import Dict, Iterable, List

CARRY_FILE = "shared/carry.json"
SOURCE_PREFIX = "shared/"
PLUGINS_PREFIX = "plugins/"

# Невидимі позначки, які відрізняють копію від джерела непомітно для ока.
INVISIBLE_MARKS = ("\u200b", "\u200c", "\u200d", "\u2060", "\ufeff", "\u00ad")


@dataclass(frozen=True)
class Finding:
    code: str
    path: str
    plugin: str
    detail: str


@dataclass
class Plan:
    findings: List[Finding] = field(default_factory=list)
    checked: int = 0  # скільки копій порівняно
    plugins: int = 0  # у скількох плагінах


class MemoryTree:
    """Дерево файлів у памʼяті: шлях від кореня репозиторію (з /) -> байти."""

    def __init__(self, files: Dict[str, bytes]):
        self.files = files

    def list_paths(self) -> List[str]:
        return sorted(self.files)

    def read(self, path: str) -> bytes:
        return self.files[path]


def copy_path(plugin: str, rel: str) -> str:
    return f"{PLUGINS_PREFIX}{plugin}/skills/{plugin}/{rel}"


def source_paths(tree) -> List[str]:
    """Спільні файли в shared/, без carry.json."""
    return [
        p[len(SOURCE_PREFIX):]
        for p in tree.list_paths()
        if p.startswith(SOURCE_PREFIX) and p != CARRY_FILE
    ]


def plugin_names(tree) -> List[str]:
    names = set()
    for p in tree.list_paths():
        if p.startswith(PLUGINS_PREFIX):
            names.add(p[len(PLUGINS_PREFIX):].split("/", 1)[0])
    return sorted(names)


def load_carry(raw: bytes) -> Dict[str, List[str]]:
    return json.loads(raw.decode("utf-8"))


def _leaves_folder(rel: str) -> bool:
    if rel.startswith("/") or "\\" in rel or ":" in rel:
        return True
    return ".." in rel.split("/")


def _entry_findings(rel, plugins, sources, known) -> List[Finding]:
    if _leaves_folder(rel):
        return [Finding("shared.carry_entry", rel, "", "plugin path leaves the plugin folder")]
    out = []
    if rel not in sources:
        out.append(Finding("shared.carry_entry", rel, "", "shared source does not hold this file"))
    if not isinstance(plugins, list) or not all(isinstance(p, str) for p in plugins):
        return out + [Finding("shared.carry_entry", rel, "", "plugin list is not a list of names")]
    for p in plugins:
        if p in ("", ".", "..") or "/" in p or "\\" in p:
            out.append(Finding("shared.carry_entry", rel, p, "plugin path leaves the plugin folder"))
        elif p not in known:
            out.append(Finding("shared.carry_entry", rel, p, "plugin folder does not exist under plugins/"))
    return out


def validate_carry(carry, source: Iterable[str], plugins: Iterable[str]) -> List[Finding]:
    """Усі хибні записи carry-списку та спільні файли, яких не несе жоден плагін."""
    sources, known = set(source), set(plugins)
    findings: List[Finding] = []
    for rel, who in carry.items():
        findings.extend(_entry_findings(rel, who, sources, known))
    for rel in sorted(sources):
        if not carry.get(rel):
            findings.append(Finding("shared.orphan_source", rel, "", "no plugin carries this shared file"))
    return findings


def _classify(shared: bytes, copy: bytes, rel: str):
    if shared == copy:
        return None
    if shared == copy.replace(b"\r\n", b"\n"):
        return "shared.line_endings", "copy differs only in line endings"
    try:
        if shared.decode("utf-8") == _strip_marks(copy.decode("utf-8")):
            return "shared.differing", "copy differs only in an invisible mark"
    except UnicodeDecodeError:
        pass
    return "shared.differing", f"copy differs from {SOURCE_PREFIX}{rel}"


def _strip_marks(text: str) -> str:
    for mark in INVISIBLE_MARKS:
        text = text.replace(mark, "")
    return text


def build_plan(tree, carry) -> Plan:
    """Єдиний план для check і sync: лише читає, нічого не пише."""
    sources, known = source_paths(tree), plugin_names(tree)
    plan = Plan()
    wrong = set()
    for f in validate_carry(carry, sources, known):
        plan.findings.append(f)
        if f.code == "shared.carry_entry":
            wrong.add(f.path)
    present = set(tree.list_paths())
    carrying = set()
    for rel in sources:
        if rel in wrong or rel not in carry:
            continue
        wanted = carry[rel]
        shared = tree.read(SOURCE_PREFIX + rel)
        for plugin in wanted:
            carrying.add(plugin)
            path = copy_path(plugin, rel)
            if path not in present:
                plan.findings.append(Finding("shared.missing", rel, plugin, "copy is not present"))
                continue
            plan.checked += 1
            verdict = _classify(shared, tree.read(path), rel)
            if verdict:
                plan.findings.append(Finding(verdict[0], rel, plugin, verdict[1]))
        for plugin in known:
            if plugin not in wanted and copy_path(plugin, rel) in present:
                plan.findings.append(
                    Finding("shared.unlisted", rel, plugin, "file is not given to this plugin by shared/carry.json")
                )
    plan.plugins = len(carrying)
    return plan


class CannotRun(Exception):
    """Запуск неможливий: нечитаний файл, зіпсований carry.json, хибне виклик."""


class FolderTree:
    """Робоча папка: читає shared/ і plugins/ від кореня репозиторію."""

    def __init__(self, root):
        self.root = str(root)

    def list_paths(self) -> List[str]:
        found = []
        for top in ("shared", "plugins"):
            base = os.path.join(self.root, top)
            for folder, _dirs, names in os.walk(base):
                for name in names:
                    rel = os.path.relpath(os.path.join(folder, name), self.root)
                    found.append(rel.replace(os.sep, "/"))
        return sorted(found)

    def read(self, path: str) -> bytes:
        with open(os.path.join(self.root, *path.split("/")), "rb") as handle:
            return handle.read()


OVERWRITE_NOTICE = (
    "note: plugin copies are overwritten by the shared source (shared/); "
    "a change made in a copy must be moved to shared/ before running sync"
)
NOTICE_CODES = ("shared.differing", "shared.line_endings", "shared.missing")
USAGE = "usage: python tools/shared_sync.py check [--staged] | sync"


def finding_line(finding: Finding) -> str:
    who = " ".join(part for part in (finding.path, finding.plugin, finding.detail) if part)
    return f"error {finding.code}: {who}"


def render_check(plan: Plan) -> List[str]:
    """Звіт check: рядки знахідок, застереження про перезапис, підсумок."""
    if not plan.findings:
        return [f"checked {plan.checked} files in {plan.plugins} plugins", "result: passed"]
    lines = [finding_line(f) for f in plan.findings]
    if any(f.code in NOTICE_CODES for f in plan.findings):
        lines.append(OVERWRITE_NOTICE)
    lines.append("result: failed")
    return lines


def load_carry_from(tree) -> Dict[str, List[str]]:
    try:
        carry = load_carry(tree.read(CARRY_FILE))
    except (OSError, ValueError) as exc:
        raise CannotRun(f"{CARRY_FILE} could not be read: {exc}")
    if not isinstance(carry, dict):
        raise CannotRun(f"{CARRY_FILE} must hold an object")
    return carry


def check_command(tree):
    plan = build_plan(tree, load_carry_from(tree))
    return render_check(plan), (3 if plan.findings else 0)


def parse_args(argv):
    if len(argv) == 1 and argv[0] in ("check", "sync"):
        return argv[0], False
    if argv == ["check", "--staged"]:
        return "check", True
    raise CannotRun(USAGE)


def default_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(argv=None, root=None) -> int:
    """Коди виходу: 0 — гаразд, 3 — розбіжність, 4 — не вдалося запустити."""
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        command, staged = parse_args(argv)
        if command != "check":
            raise CannotRun(USAGE)
        lines, code = check_command(FolderTree(root or default_root()))
        for line in lines:
            print(line)
        return code
    except Exception as exc:  # CannotRun і будь-який збій — код 4, ніколи 1
        print(f"error shared.cannot_run: {exc}", file=sys.stderr)
    return 4


if __name__ == "__main__":
    sys.exit(main())
