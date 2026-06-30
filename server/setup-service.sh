#!/bin/bash
# ============================================================
# Setup systemd service + Nginx reverse proxy
# Run as: sudo bash setup-service.sh
# ============================================================

set -e

DOMAIN=${1:-"your-domain.com"}   # pass your domain as arg: bash setup-service.sh mydomain.com

echo "======================================================"
echo "  Setting up systemd service + Nginx"
echo "  Domain: $DOMAIN"
echo "======================================================"

# ── Systemd Service ────────────────────────────────────────
echo "[1/3] Creating systemd service..."
cat > /etc/systemd/system/lottery-api.service <<EOF
[Unit]
Description=Lottery Dashboard FastAPI
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/lottery/backend
Environment=PATH=/opt/lottery/venv/bin
EnvironmentFile=/opt/lottery/backend/.env
ExecStart=/opt/lottery/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable lottery-api
systemctl start lottery-api
echo "  FastAPI service started on port 8000"

# ── Nginx Config ───────────────────────────────────────────
echo "[2/3] Configuring Nginx..."
cat > /etc/nginx/sites-available/lottery <<EOF
server {
    listen 80;
    server_name $DOMAIN;

    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=api:10m rate=30r/m;

    location /api/ {
        limit_req zone=api burst=10 nodelay;
        proxy_pass         http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header   Host              \$host;
        proxy_set_header   X-Real-IP         \$remote_addr;
        proxy_set_header   X-Forwarded-For   \$proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto \$scheme;
        proxy_read_timeout 120;
    }

    location / {
        return 301 https://\$host\$request_uri;
    }
}
EOF

ln -sf /etc/nginx/sites-available/lottery /etc/nginx/sites-enabled/lottery
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx
echo "  Nginx configured"

# ── SSL Certificate ────────────────────────────────────────
echo "[3/3] Getting SSL certificate..."
certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos -m "admin@$DOMAIN" || \
  echo "  ⚠️  SSL skipped — add your email and try: certbot --nginx -d $DOMAIN"

echo ""
echo "======================================================"
echo "  Done!"
echo "  API running at: https://$DOMAIN/api/"
echo "  Check status:   systemctl status lottery-api"
echo "  View logs:      journalctl -u lottery-api -f"
echo "======================================================"
