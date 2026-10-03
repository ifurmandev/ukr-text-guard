#!/usr/bin/env bash
# Тонкий делегат: знаходить робочий Python і передає всі аргументи раннеру.
# Вердиктів тут немає, вони живуть у run_eval.py.
here="$(cd "$(dirname "$0")" && pwd)"
for cand in python3 python py; do
  if "$cand" -c "import sys" >/dev/null 2>&1; then
    exec "$cand" "$here/run_eval.py" "$@"
  fi
done
echo "run.sh: no working Python found (tried python3, python, py)" >&2
exit 1
