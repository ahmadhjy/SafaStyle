#!/usr/bin/env bash
# Run on the server after each git push. Pulls code, installs deps, migrates, restarts.
set -euo pipefail

APP_DIR="${APP_DIR:-/var/www/safastyle}"
VENV="${APP_DIR}/venv"
SERVICE="${GUNICORN_SERVICE:-gunicorn-safastyle}"

cd "$APP_DIR"

echo "==> Pull latest code"
git pull --ff-only origin main

echo "==> Install Python dependencies"
"${VENV}/bin/pip" install -r requirements.txt --quiet

echo "==> Django migrate + static"
"${VENV}/bin/python" manage.py migrate --noinput
"${VENV}/bin/python" manage.py collectstatic --noinput

if [ -f .env ]; then
  chown www-data:www-data .env
  chmod 640 .env
fi

echo "==> Restart Gunicorn"
sudo systemctl restart "${SERVICE}"

echo "==> Done — https://safastyle.com is live with the latest code."
