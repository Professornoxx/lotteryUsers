#!/bin/bash
# ============================================================
# Oracle Cloud VM - Full Server Setup Script
# OS: Ubuntu 22.04 (Oracle Always Free ARM)
# Run as: sudo bash setup.sh
# ============================================================

set -e
echo "======================================================"
echo "  Lottery Dashboard - Oracle Cloud VM Setup"
echo "======================================================"

# ── System Update ──────────────────────────────────────────
echo "[1/8] Updating system..."
apt-get update -y && apt-get upgrade -y
apt-get install -y curl wget git unzip software-properties-common \
  build-essential libssl-dev libffi-dev python3-dev \
  nginx certbot python3-certbot-nginx ufw

# ── Python 3.11 ────────────────────────────────────────────
echo "[2/8] Installing Python 3.11..."
add-apt-repository ppa:deadsnakes/ppa -y
apt-get update -y
apt-get install -y python3.11 python3.11-venv python3.11-dev pip

# ── Oracle Instant Client (required for oracledb) ──────────
echo "[3/8] Installing Oracle Instant Client..."
wget -q https://download.oracle.com/otn_software/linux/instantclient/2340000/instantclient-basiclite-linux.x64-23.4.0.24.05.zip -O /tmp/ic.zip
mkdir -p /opt/oracle
unzip -q /tmp/ic.zip -d /opt/oracle
echo /opt/oracle/instantclient_23_4 > /etc/ld.so.conf.d/oracle-instantclient.conf
ldconfig
echo "export LD_LIBRARY_PATH=/opt/oracle/instantclient_23_4:\$LD_LIBRARY_PATH" >> /etc/environment

# ── Oracle Database XE 21c ─────────────────────────────────
echo "[4/8] Installing Oracle Database XE 21c..."
wget -q https://download.oracle.com/otn-pub/otn_software/db-express/oracle-database-xe-21c-1.0-1.ol8.x86_64.rpm -O /tmp/oracle-xe.rpm 2>/dev/null || true
# Note: If download fails, follow manual install at: https://www.oracle.com/database/technologies/xe-downloads.html
# For ARM (Ampere), use Oracle DB Free 23c instead:
# https://www.oracle.com/database/free/get-started/

# ── App Directory & Clone ──────────────────────────────────
echo "[5/8] Setting up application directory..."
mkdir -p /opt/lottery
cd /opt/lottery

if [ -d ".git" ]; then
  git pull origin main
else
  git clone https://github.com/Professornoxx/lotteryUsers.git .
fi

# ── Python Virtual Environment ─────────────────────────────
echo "[6/8] Installing Python dependencies..."
python3.11 -m venv /opt/lottery/venv
source /opt/lottery/venv/bin/activate
pip install --upgrade pip
pip install -r /opt/lottery/backend/requirements.txt

# ── Environment File ───────────────────────────────────────
echo "[7/8] Creating .env file..."
if [ ! -f /opt/lottery/backend/.env ]; then
  cp /opt/lottery/backend/.env.example /opt/lottery/backend/.env
  echo ""
  echo "⚠️  IMPORTANT: Edit /opt/lottery/backend/.env with your real values:"
  echo "    nano /opt/lottery/backend/.env"
fi

# ── Firewall ───────────────────────────────────────────────
echo "[8/8] Configuring firewall..."
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw allow 8000
ufw --force enable

echo ""
echo "======================================================"
echo "  Setup complete!"
echo "  Next steps:"
echo "  1. Edit: nano /opt/lottery/backend/.env"
echo "  2. Run:  bash /opt/lottery/server/setup-oracle-db.sh"
echo "  3. Run:  bash /opt/lottery/server/setup-service.sh"
echo "======================================================"
