#!/bin/bash
# ============================================================
# Zayro Teams — Full Deployment Script
# Server: 187.127.131.93  Port: 8030
# Run as root or sudo user on Ubuntu/Debian
# Usage: bash deploy.sh
# ============================================================

set -e

PROJECT_DIR="/var/www/zayro_teams"
REPO_URL="https://github.com/zayroninfotech/Zayro_Teams.git"
VENV_DIR="$PROJECT_DIR/venv"
SERVICE_NAME="zayro_teams"
PORT=8030

echo "=============================="
echo " Zayro Teams Deployment Start"
echo "=============================="

# 1. System packages
echo "[1/8] Installing system packages..."
apt-get update -y
apt-get install -y python3 python3-pip python3-venv git nginx

# 2. Clone or pull repo
echo "[2/8] Cloning/updating repository..."
if [ -d "$PROJECT_DIR/.git" ]; then
    cd "$PROJECT_DIR"
    git pull origin main
else
    git clone "$REPO_URL" "$PROJECT_DIR"
    cd "$PROJECT_DIR"
fi

# 3. Virtual environment
echo "[3/8] Setting up Python virtual environment..."
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r requirements.txt

# 4. Django setup
echo "[4/8] Running Django migrations and collectstatic..."
python manage.py migrate --noinput
python manage.py collectstatic --noinput

# 5. Create media/static dirs
mkdir -p "$PROJECT_DIR/media"
mkdir -p "$PROJECT_DIR/staticfiles"

# 6. Systemd service for Daphne (ASGI — handles HTTP + WebSocket)
echo "[5/8] Creating systemd service..."
cat > /etc/systemd/system/${SERVICE_NAME}.service <<EOF
[Unit]
Description=Zayro Teams - Daphne ASGI Server
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=${PROJECT_DIR}
ExecStart=${VENV_DIR}/bin/daphne -b 127.0.0.1 -p 8031 zayro_teams.asgi:application
Restart=always
RestartSec=3
Environment=DJANGO_SETTINGS_MODULE=zayro_teams.settings

[Install]
WantedBy=multi-user.target
EOF

chown -R www-data:www-data "$PROJECT_DIR"
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"

# 7. Nginx config — exposes on port 8030
echo "[6/8] Configuring Nginx on port 8030..."
cat > /etc/nginx/sites-available/${SERVICE_NAME} <<'EOF'
server {
    listen 8030;
    server_name 187.127.131.93;

    client_max_body_size 20M;

    location /static/ {
        alias /var/www/zayro_teams/staticfiles/;
    }

    location /media/ {
        alias /var/www/zayro_teams/media/;
    }

    # WebSocket upgrade
    location /ws/ {
        proxy_pass http://127.0.0.1:8031;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400;
    }

    # Regular HTTP
    location / {
        proxy_pass http://127.0.0.1:8031;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
EOF

ln -sf /etc/nginx/sites-available/${SERVICE_NAME} /etc/nginx/sites-enabled/${SERVICE_NAME}
nginx -t
systemctl reload nginx

# 8. Firewall
echo "[7/8] Opening firewall port 8030..."
if command -v ufw &>/dev/null; then
    ufw allow 8030/tcp
fi

echo ""
echo "=============================="
echo " Deployment Complete!"
echo " App running at: http://187.127.131.93:8030"
echo "=============================="
