#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd "$(dirname "$0")" && pwd)"
if [ ! -x "$project_dir/server/.venv/bin/python" ]; then
  echo "Backend setup is missing. Follow server/README.md first." >&2
  exit 1
fi
exec "$project_dir/server/.venv/bin/python" "$project_dir/scripts/run.py" "$@"
