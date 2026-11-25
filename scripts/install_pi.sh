#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$PROJECT_DIR/.venv"

sudo apt-get update
sudo apt-get install -y python3-venv python3-tk python3-gpiozero alsa-utils espeak-ng
python3 -m venv "$VENV"
"$VENV/bin/python" -m pip install --upgrade pip
chmod +x "$PROJECT_DIR/scripts/start_robot.sh"

# Start with the desktop after login or reboot. This inherits the
# graphical session, so the Tk window has a display. Raspberry Pi OS
# Desktop auto-logins by default.
mkdir -p "$HOME/.config/autostart"
sed "s|__PROJECT_DIR__|$PROJECT_DIR|g" "$PROJECT_DIR/autostart/desk-robot.desktop" \
  > "$HOME/.config/autostart/desk-robot.desktop"

# Optional systemd unit, kept as a backup. It is not enabled here, so
# the face is not launched twice. If you prefer systemd instead of the
# autostart file, remove the .desktop file, then run:
#   loginctl enable-linger "$USER"
#   systemctl --user daemon-reload
#   systemctl --user enable --now desk-robot.service
mkdir -p "$HOME/.config/systemd/user"
sed "s|__PROJECT_DIR__|$PROJECT_DIR|g" "$PROJECT_DIR/systemd/desk-robot.service" \
  > "$HOME/.config/systemd/user/desk-robot.service"
systemctl --user daemon-reload || true

echo "Installed. Copy .env.example to .env if needed, add XAI_API_KEY, then reboot."
echo "The face starts with the desktop after login (auto-login is the Pi OS default)."
