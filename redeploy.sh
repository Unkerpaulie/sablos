#!/usr/bin/env bash
# Pull latest code, refresh dependencies, run migrations, collect static,
# and restart the gunicorn service.
#
# Run as the application user (e.g. `deploy`):
#
#   ./redeploy.sh             # pulls, runs migrations + collectstatic, restarts
#   SKIP_MIGRATE=1 ./redeploy.sh   # skip migrations
#   BRANCH=main ./redeploy.sh      # check out a specific branch (default: current)
#
# The script aborts on any error and leaves the running service untouched
# if migrations or collectstatic fail.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

VENV="$REPO_ROOT/.venv"
SERVICE="${SERVICE:-sablos}"
SKIP_MIGRATE="${SKIP_MIGRATE:-0}"
BRANCH="${BRANCH:-}"

if [[ ! -d "$VENV" ]]; then
    echo "ERROR: virtualenv not found at $VENV. Run ./launch.sh first."
    exit 1
fi
if [[ ! -f "$REPO_ROOT/.env" ]]; then
    echo "ERROR: $REPO_ROOT/.env is missing."
    exit 1
fi

echo "==> Backing up SQLite database"
TS="$(date +%Y%m%d-%H%M%S)"
mkdir -p "$REPO_ROOT/backups"
if [[ -f "$REPO_ROOT/db.sqlite3" ]]; then
    cp "$REPO_ROOT/db.sqlite3" "$REPO_ROOT/backups/db.sqlite3.$TS"
    echo "    Saved backups/db.sqlite3.$TS"
fi

echo "==> Pulling latest code"
git fetch --prune
if [[ -n "$BRANCH" ]]; then
    git checkout "$BRANCH"
fi
git pull --ff-only

# shellcheck source=/dev/null
source "$VENV/bin/activate"
export $(grep -v '^#' "$REPO_ROOT/.env" | xargs -d '\n')

echo "==> Installing / updating dependencies"
pip install --upgrade pip wheel >/dev/null
pip install -r requirements.txt

if [[ "$SKIP_MIGRATE" != "1" ]]; then
    echo "==> Running migrations"
    python manage.py migrate --noinput
fi

echo "==> Collecting static files"
python manage.py collectstatic --noinput

echo "==> Running deployment checks"
python manage.py check --deploy || true

echo "==> Restarting $SERVICE"
sudo systemctl restart "$SERVICE"
sudo systemctl --no-pager --full status "$SERVICE" | head -n 20

echo "==> Pruning old backups (keep last 10)"
ls -1t "$REPO_ROOT/backups"/db.sqlite3.* 2>/dev/null | tail -n +11 | xargs -r rm -f

echo "==> Redeploy complete."
