#!/usr/bin/env bash
# Launch the desk robot display. Used by desktop autostart on the Pi.
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$PROJECT_DIR/src"
cd "$PROJECT_DIR"
if [ -x "$PROJECT_DIR/.venv/bin/python" ]; then
  exec "$PROJECT_DIR/.venv/bin/python" -m robot_display "$@"
fi
exec python3 -m robot_display "$@"
