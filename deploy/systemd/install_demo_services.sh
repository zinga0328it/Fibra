#!/bin/bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"

echo "Copying FTTH systemd service files to /etc/systemd/system/"
sudo cp "$HERE/ftth.service" /etc/systemd/system/ftth.service
sudo cp "$HERE/bot.service" /etc/systemd/system/ftth-bot.service

# Reload systemd to read new unit files
sudo systemctl daemon-reload
# Enable and start services
sudo systemctl enable --now ftth.service
sudo systemctl enable --now ftth-bot.service

# Show statuses
sudo systemctl status --no-pager ftth.service ftth-bot.service || true

echo "Done. Services installed and started. To remove after the presentation, run:"
echo "  sudo systemctl disable --now ftth.service ftth-bot.service"
echo "  sudo rm /etc/systemd/system/ftth.service /etc/systemd/system/ftth-bot.service"
echo "  sudo systemctl daemon-reload"
