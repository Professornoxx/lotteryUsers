#!/bin/bash
# ============================================================
# Deploy script — called by GitHub Actions on every push
# ============================================================

set -e

echo "[deploy] Pulling latest code..."
cd /opt/lottery
git pull origin main

echo "[deploy] Installing dependencies..."
source /opt/lottery/venv/bin/activate
pip install -r backend/requirements.txt --quiet

echo "[deploy] Restarting service..."
sudo systemctl restart lottery-api

echo "[deploy] Done — $(date)"
systemctl status lottery-api --no-pager
