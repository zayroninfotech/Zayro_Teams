#!/bin/bash
# ============================================================
# MongoDB Install + Setup for Zayro Teams
# Server: 187.127.131.93
# Run as root: bash mongo_install.sh
# ============================================================

set -e

echo "=============================="
echo " MongoDB Setup — Zayro Teams"
echo "=============================="

# 1. Install MongoDB
echo "[1/4] Installing MongoDB..."
apt-get update -y
apt-get install -y gnupg curl

curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | \
  gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor

echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] \
https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" \
  > /etc/apt/sources.list.d/mongodb-org-7.0.list

apt-get update -y
apt-get install -y mongodb-org

# 2. Start MongoDB
echo "[2/4] Starting MongoDB..."
systemctl enable mongod
systemctl start mongod
sleep 3

# 3. Run setup script (create user + collections)
echo "[3/4] Creating database, user, and collections..."
# Credentials are read from environment — set them before running this script:
#   export MONGO_USER=vamsi
#   export MONGO_PASS=your_password
MONGO_USER=${MONGO_USER:-vamsi} MONGO_PASS="$MONGO_PASS" \
  mongosh --quiet /var/www/zayro_teams/mongo_setup.js

# 4. Enable MongoDB auth
echo "[4/4] Enabling MongoDB authentication..."
cat > /etc/mongod.conf << 'EOF'
storage:
  dbPath: /var/lib/mongodb

systemLog:
  destination: file
  logAppend: true
  path: /var/log/mongodb/mongod.log

net:
  port: 27017
  bindIp: 127.0.0.1

security:
  authorization: enabled

processManagement:
  timeZoneInfo: /usr/share/zoneinfo
EOF

systemctl restart mongod

echo ""
echo "=============================="
echo " MongoDB Ready!"
echo " Connection string:"
echo " mongodb://${MONGO_USER}:****@127.0.0.1:27017/zayro_teams"
echo "=============================="
