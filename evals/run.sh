#!/usr/bin/env bash
# Прогін усіх зразків через аналізатор: назва → індекс
cd "$(dirname "$0")/.."
for f in evals/samples/*.txt; do
  printf "%-40s " "$(basename "$f" .txt)"
  python3 plugins/ukr-text-guard/skills/ukr-text-guard/scripts/analyze.py "$f" | head -1
done
