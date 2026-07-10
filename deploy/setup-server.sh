#!/usr/bin/env bash
# ONE-TIME server bootstrap for Ubuntu 22/24 on DigitalOcean.
# Run as root on the droplet:
#   curl -sSL https://raw.githubusercontent.com/ahmadhjy/SafaStyle/main/deploy/setup-server.sh | bash
# Or paste after cloning the repo.
set -euo pipefail

APP_DIR="/var/www/safastyle"
REPO="https://github.com/ahmadhjy/SafaStyle.git"
DOMAIN="safastyle.com"
DB_NAME="safastyle"
DB_USER="safastyle"
DB_PASS="${DB_PASS:-$(openssl rand -hex 16)}"

echo "==> System packages"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq git python3 python3-venv python3-pip nginx postgresql \
  postgresql-contrib certbot python3-certbot-nginx ufw

echo "==> Firewall"
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

echo "==> PostgreSQL database"
sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='${DB_USER}'" | grep -q 1 \
  || sudo -u postgres psql -c "CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASS}';"
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" | grep -q 1 \
  || sudo -u postgres psql -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};"

echo "==> Clone application"
mkdir -p /var/www
if [ ! -d "${APP_DIR}/.git" ]; then
  git clone "${REPO}" "${APP_DIR}"
else
  cd "${APP_DIR}" && git pull
fi
cd "${APP_DIR}"

echo "==> Python virtualenv"
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

echo "==> Production .env (edit email password after setup)"
if [ ! -f .env ]; then
  SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")
  cat > .env <<EOF
DEBUG=false
SECRET_KEY=${SECRET}
ALLOWED_HOSTS=safastyle.com,www.safastyle.com,209.38.211.102
CSRF_TRUSTED_ORIGINS=https://safastyle.com,https://www.safastyle.com
SITE_URL=https://safastyle.com

DB_ENGINE=postgresql
DB_NAME=${DB_NAME}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASS}
DB_HOST=localhost
DB_PORT=5432

EMAIL_HOST=smtp.ionos.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=info@safastyle.com
EMAIL_HOST_PASSWORD=CHANGE_ME
DEFAULT_FROM_EMAIL=Safa Style <info@safastyle.com>
ORDER_NOTIFICATION_EMAILS=info@safastyle.com,sales@safastyle.com
CONTACT_EMAIL=info@safastyle.com
EOF
  chmod 600 .env
  echo "    Created .env — set EMAIL_HOST_PASSWORD before going live."
fi

echo "==> Django setup"
./venv/bin/python manage.py migrate --noinput
./venv/bin/python manage.py prepare_launch || true
./venv/bin/python manage.py collectstatic --noinput

echo "==> Gunicorn systemd service"
cp deploy/gunicorn.service /etc/systemd/system/gunicorn-safastyle.service
systemctl daemon-reload
systemctl enable gunicorn-safastyle
systemctl restart gunicorn-safastyle

echo "==> Nginx"
cp deploy/nginx.conf /etc/nginx/sites-available/safastyle
ln -sf /etc/nginx/sites-available/safastyle /etc/nginx/sites-enabled/safastyle
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

echo "==> SSL certificate (Let's Encrypt)"
certbot --nginx -d "${DOMAIN}" -d "www.${DOMAIN}" --non-interactive --agree-tos \
  -m info@safastyle.com --redirect || echo "Certbot skipped — run manually when DNS has propagated."

mkdir -p media staticfiles
chown -R www-data:www-data media staticfiles

echo ""
echo "============================================"
echo "  Safa Style server is ready."
echo "  Site:  https://${DOMAIN}"
echo "  Admin: https://${DOMAIN}/admin/"
echo ""
echo "  DB password (saved in ${APP_DIR}/.env):"
echo "  ${DB_PASS}"
echo ""
echo "  Create admin user:"
echo "  cd ${APP_DIR} && ./venv/bin/python manage.py createsuperuser"
echo "============================================"
