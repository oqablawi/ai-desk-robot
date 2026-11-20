#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$PROJECT_DIR/.venv"

sudo apt-get update
sudo apt-get install -y python3-venv python3-tk
python3 -m venv "$VENV"
"$VENV/bin/python" -m pip install --upgrade pip

mkdir -p "$HOME/.config/systemd/user"
sed "s|__PROJECT_DIR__|$PROJECT_DIR|g" "$PROJECT_DIR/systemd/desk-robot.service" \
  > "$HOME/.config/systemd/user/desk-robot.service"
systemctl --user daemon-reload
systemctl --user enable desk-robot.service

echo "Installed. Copy .env.example to .env, edit it, then reboot."
