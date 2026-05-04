#!/usr/bin/env bash
# First-time bring-up of sablos on an Ubuntu host.
#
# Run this from the repo root as the application user (e.g. `deploy`).
# It is idempotent: re-running it will not destroy data.
#
#   ./launch.sh
#
# What it does:
#   1. Creates .venv if missing
#   2. Installs Python dependencies
#   3. Verifies a .env file exists
#   4. Runs migrations
#   5. Collects static files into staticfiles/
#   6. Optionally creates a superuser
#   7. Prints the systemd / nginx commands you still need to run as root

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

VENV="$REPO_ROOT/.venv"
PY_BIN="${PY_BIN:-python3}"

echo "==> Project root: $REPO_ROOT"

# 1. Virtualenv
if [[ ! -d "$VENV" ]]; then
    echo "==> Creating virtualenv at $VENV"
    "$PY_BIN" -m venv "$VENV"
else
    echo "==> Virtualenv already exists, reusing"
fi

# shellcheck source=/dev/null
source "$VENV/bin/activate"

# 2. Dependencies
echo "==> Installing Python dependencies"
pip install --upgrade pip wheel >/dev/null
pip install -r requirements.txt

# 3. Environment file
if [[ ! -f "$REPO_ROOT/.env" ]]; then
    echo "ERROR: $REPO_ROOT/.env is missing."
    echo "       Copy deploy/.env.prod.example to .env and fill in real values."
    exit 1
fi
export $(grep -v '^#' "$REPO_ROOT/.env" | xargs -d '\n')

# 4. Migrations
echo "==> Applying migrations"
python manage.py migrate --noinput

# 5. Static files
echo "==> Collecting static files"
python manage.py collectstatic --noinput

# 6. Superuser (optional, only if none exists)
HAS_SUPERUSER="$(python manage.py shell -c \
    'from django.contrib.auth import get_user_model; \
     print("yes" if get_user_model().objects.filter(is_superuser=True).exists() else "no")' \
    | tail -n 1)"
if [[ "$HAS_SUPERUSER" == "no" ]]; then
    echo "==> No superuser found. Create one now? [y/N]"
    read -r CREATE_SU
    if [[ "$CREATE_SU" =~ ^[Yy]$ ]]; then
        python manage.py createsuperuser
    else
        echo "    Skipping superuser creation. Run 'python manage.py createsuperuser' later."
    fi
else
    echo "==> Superuser already exists, skipping prompt"
fi

# 7. Permissions hint for the SQLite file
chmod 640 "$REPO_ROOT/db.sqlite3" || true

cat <<'EOM'

==> Application bootstrap complete.

Next steps (one-time, as root):

  1. Install the systemd unit:
       sudo cp deploy/sablos.service /etc/systemd/system/sablos.service
       sudo systemctl daemon-reload
       sudo systemctl enable --now sablos
       sudo systemctl status sablos

  2. Install the nginx site:
       sudo cp deploy/sablos.nginx.conf /etc/nginx/sites-available/sablos
       sudo ln -sf /etc/nginx/sites-available/sablos /etc/nginx/sites-enabled/sablos
       sudo nginx -t && sudo systemctl reload nginx

  3. Issue a TLS certificate (after DNS points at this server):
       sudo certbot --nginx -d example.com -d www.example.com

See launch.md for the full walkthrough.
EOM
