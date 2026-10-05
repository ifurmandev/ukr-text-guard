#!/usr/bin/env bash
# Тонкий делегат: знаходить робочий Python, спершу перевіряє, що копії спільних
# файлів у плагінах збігаються з shared/, і лише тоді передає всі аргументи раннеру.
# Вердиктів тут немає: розбіжності живуть у tools/shared_sync.py, діапазони в run_eval.py.
# Коди виходу: 0 і 1 від раннера, 3 розбіжність копій, 4 перевірку не вдалося запустити.
here="$(cd "$(dirname "$0")" && pwd)"
for cand in python3 python py; do
  if "$cand" -c "import sys" >/dev/null 2>&1; then
    # Перевіряється весь репозиторій, усі плагіни, незалежно від аргументів.
    "$cand" "$here/../tools/shared_sync.py" check
    code=$?
    case "$code" in
      0) exec "$cand" "$here/run_eval.py" "$@" ;;
      3) echo "run.sh: the eval did not run, the cause is a divergence (not a failed band)" >&2
         exit 3 ;;
      *) echo "run.sh: the eval did not run, the check could not run (exit code $code)" >&2
         exit 4 ;;
    esac
  fi
done
echo "run.sh: the eval did not run, the check could not run: no working Python found (tried python3, python, py)" >&2
exit 4
