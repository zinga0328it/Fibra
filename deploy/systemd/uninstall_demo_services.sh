#!/bin/bash
set -euo pipefail

echo "Disabling and stopping FTTH services"
sudo systemctl disable --now ftth.service || true
sudo systemctl disable --now ftth-bot.service || true

# Remove unit files
sudo rm -f /etc/systemd/system/ftth.service /etc/systemd/system/ftth-bot.service || true

# Reload systemd
sudo systemctl daemon-reload
sudo systemctl reset-failed || true

echo "Uninstalled ftth and ftth-bot services. You may also remove any environment/drop-in files if used."
