#!/bin/bash
# Production server setup script for Massage Marketplace.
# Run as root on a fresh Ubuntu 22.04+ VPS.
#
# Usage:
#   sudo bash deploy/setup.sh

set -euo pipefail

APP_USER="marketplace"
APP_DIR="/opt/marketplace"
DOMAIN="${1:-YOUR_DOMAIN}"

echo "=== Massage Marketplace - Server Setup ==="
echo "Domain: ${DOMAIN}"
echo ""

# ---- System packages ----
echo "[1/8] Installing system packages..."
apt-get update -qq
apt-get install -y -qq \
    python3 python3-pip python3-venv \
    postgresql postgresql-contrib \
    nginx certbot python3-certbot-nginx \
    git curl

# ---- Create application user ----
echo "[2/8] Creating application user..."
if ! id "${APP_USER}" &>/dev/null; then
    useradd --system --shell /bin/bash --home "${APP_DIR}" "${APP_USER}"
fi

# ---- Setup application directory ----
echo "[3/8] Setting up application directory..."
mkdir -p "${APP_DIR}"
mkdir -p /var/log/marketplace
mkdir -p /var/backups/marketplace
chown -R "${APP_USER}:www-data" "${APP_DIR}"
chown -R "${APP_USER}:www-data" /var/log/marketplace

# ---- PostgreSQL setup ----
echo "[4/8] Configuring PostgreSQL..."
sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='${APP_USER}'" | grep -q 1 || \
    sudo -u postgres createuser "${APP_USER}"
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='massage_marketplace'" | grep -q 1 || \
    sudo -u postgres createdb -O "${APP_USER}" massage_marketplace

# ---- Python virtual environment ----
echo "[5/8] Setting up Python environment..."
sudo -u "${APP_USER}" python3 -m venv "${APP_DIR}/venv"
sudo -u "${APP_USER}" "${APP_DIR}/venv/bin/pip" install --upgrade pip
sudo -u "${APP_USER}" "${APP_DIR}/venv/bin/pip" install -r "${APP_DIR}/requirements.txt"
sudo -u "${APP_USER}" "${APP_DIR}/venv/bin/pip" install gunicorn

# ---- Collect static files ----
echo "[6/8] Collecting static files..."
sudo -u "${APP_USER}" bash -c "cd ${APP_DIR} && source venv/bin/activate && python marketplace/manage.py collectstatic --noinput"

# ---- Run migrations ----
echo "[6/8] Running database migrations..."
sudo -u "${APP_USER}" bash -c "cd ${APP_DIR} && source venv/bin/activate && python marketplace/manage.py migrate --noinput"

# ---- Systemd service ----
echo "[7/8] Installing systemd service..."
cp "${APP_DIR}/deploy/marketplace.service" /etc/systemd/system/marketplace.service
systemctl daemon-reload
systemctl enable marketplace
systemctl start marketplace

# ---- Nginx configuration ----
echo "[8/8] Configuring Nginx..."
sed "s/YOUR_DOMAIN/${DOMAIN}/g" "${APP_DIR}/deploy/nginx.conf" > "/etc/nginx/sites-available/marketplace"
ln -sf /etc/nginx/sites-available/marketplace.conf /etc/nginx/sites-enabled/marketplace.conf
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

# ---- SSL certificate (skip if no real domain) ----
if [ "${DOMAIN}" != "YOUR_DOMAIN" ]; then
    echo "Obtaining SSL certificate for ${DOMAIN}..."
    certbot --nginx -d "${DOMAIN}" --non-interactive --agree-tos --email "admin@${DOMAIN}" || \
        echo "WARNING: SSL certificate setup failed. Run certbot manually."
fi

# ---- Backup cron job ----
echo "Setting up daily backup cron job..."
(crontab -l 2>/dev/null || true; echo "0 2 * * * ${APP_DIR}/deploy/backup.sh >> /var/log/marketplace/backup.log 2>&1") | crontab -

echo ""
echo "=== Setup Complete ==="
echo "Application: ${APP_DIR}"
echo "Service:     systemctl status marketplace"
echo "Logs:        journalctl -u marketplace -f"
echo "Nginx:       /etc/nginx/sites-available/marketplace"
echo ""
echo "Next steps:"
echo "  1. Copy your .env file to ${APP_DIR}/.env"
echo "  2. Set DEBUG=False and configure SECRET_KEY in .env"
echo "  3. Restart: sudo systemctl restart marketplace"
echo "  4. Create superuser: sudo -u ${APP_USER} bash -c 'cd ${APP_DIR} && source venv/bin/activate && python marketplace/manage.py createsuperuser'"
