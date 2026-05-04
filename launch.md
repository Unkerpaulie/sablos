# Launching sablos on Digital Ocean

This walks through bringing the site up on a fresh Ubuntu 22.04 / 24.04
droplet. Stack: gunicorn (systemd) → unix socket → nginx → Let's Encrypt.

The two scripts (`launch.sh`, `redeploy.sh`) at the repo root do the
Python-side work; this doc covers everything around them.

## 1. Provision the droplet

1. Create a droplet — the cheapest **Regular** size is enough for a
   single-user PM tool (1 GB RAM, 1 vCPU, $6/mo at the time of writing).
2. Image: **Ubuntu 24.04 (LTS) x64**.
3. Auth: add your SSH key.
4. Hostname: anything, e.g. `sablos-prod`.
5. Once it boots, point your DNS at the droplet IP (A records for
   `example.com` and `www.example.com`).

## 2. Initial server hardening (as `root`)

SSH in: `ssh root@<droplet-ip>`

```bash
# Patch the box
apt update && apt upgrade -y

# Create the application user
adduser --disabled-password --gecos "" deploy
usermod -aG sudo deploy
mkdir -p /home/deploy/.ssh
cp ~/.ssh/authorized_keys /home/deploy/.ssh/
chown -R deploy:deploy /home/deploy/.ssh
chmod 700 /home/deploy/.ssh
chmod 600 /home/deploy/.ssh/authorized_keys

# Firewall — only SSH and HTTP/HTTPS
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

# System packages
apt install -y python3-venv python3-pip git nginx certbot python3-certbot-nginx
```

Optional but recommended: edit `/etc/ssh/sshd_config` to set
`PermitRootLogin no` and `PasswordAuthentication no`, then
`systemctl restart ssh`. From here on, log in as `deploy`.

## 3. Clone the repo (as `deploy`)

```bash
ssh deploy@<droplet-ip>
cd ~
git clone https://github.com/<your-user>/sablos_root.git
cd sablos_root
```

## 4. Configure environment variables

```bash
cp deploy/.env.prod.example .env
# Generate a strong secret key:
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
# Edit .env: paste the secret, set DJANGO_ALLOWED_HOSTS to your domain(s).
nano .env
chmod 600 .env
```

Make sure `DJANGO_SETTINGS_MODULE=config.settings.prod` is set.

## 5. Bootstrap the application

```bash
chmod +x launch.sh redeploy.sh
./launch.sh
```

The script creates `.venv`, installs dependencies, applies migrations,
collects static files into `staticfiles/`, and prompts to create a
superuser. It will then print the remaining root-level steps.

## 6. Install the systemd unit (as `root` or via `sudo`)

```bash
sudo cp deploy/sablos.service /etc/systemd/system/sablos.service
sudo systemctl daemon-reload
sudo systemctl enable --now sablos
sudo systemctl status sablos
```

If anything is wrong, `journalctl -u sablos -n 100 --no-pager` will tell
you why. The unit binds gunicorn to `/run/sablos/sablos.sock`.

## 7. Install nginx

```bash
sudo cp deploy/sablos.nginx.conf /etc/nginx/sites-available/sablos
# Edit and replace example.com with your real domain:
sudo nano /etc/nginx/sites-available/sablos
sudo ln -sf /etc/nginx/sites-available/sablos /etc/nginx/sites-enabled/sablos
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

Visit `http://example.com` — the site should load over HTTP.

## 8. TLS via Let's Encrypt

```bash
sudo certbot --nginx -d example.com -d www.example.com
```

Certbot rewrites the nginx config to add the TLS server block and a
HTTP→HTTPS redirect. The cert auto-renews via the systemd timer
(`systemctl list-timers | grep certbot` to confirm).

Because `DJANGO_SECURE_SSL_REDIRECT=true` is set in `.env`, Django will
also enforce HTTPS at the application layer.

## 9. Verify

- `https://example.com/` — public homepage.
- `https://example.com/say-hi/` — contact form.
- `https://example.com/login/` — staff login.
- `https://example.com/wip/` — dashboard (requires login).
- `https://example.com/admin/` — Django admin.

## 10. Day-to-day redeploys

After committing and pushing changes:

```bash
ssh deploy@<droplet-ip>
cd ~/sablos_root
./redeploy.sh
```

`redeploy.sh` snapshots `db.sqlite3` into `backups/`, pulls the latest
code, installs new dependencies, runs migrations, collects static, and
restarts the gunicorn service. Use `SKIP_MIGRATE=1 ./redeploy.sh` for
template-only changes.

## 11. Backups

The SQLite database is a single file, `db.sqlite3`. The simplest backup
is a periodic copy off the droplet, e.g. via cron:

```bash
crontab -e
# 03:30 every day, copy the DB file to your home dir with a timestamp
30 3 * * * cp ~/sablos_root/db.sqlite3 ~/backups/db.sqlite3.$(date +\%F)
```

For off-box durability, configure Digital Ocean weekly droplet backups
(extra ~$1.20/mo) or rsync `~/sablos_root/db.sqlite3` to S3-compatible
storage from cron.

## Troubleshooting

- **502 Bad Gateway**: gunicorn isn't running. `sudo systemctl status sablos` and `journalctl -u sablos`.
- **CSRF / DisallowedHost errors**: check `DJANGO_ALLOWED_HOSTS` in `.env` matches the URL you're using.
- **Static files missing**: re-run `./redeploy.sh` (which calls `collectstatic`), and make sure nginx's `alias` path matches `STATIC_ROOT`.
- **Permission denied on socket**: confirm the `RuntimeDirectory=sablos` line in the service file and that nginx's `www-data` user is in a position to reach `/run/sablos/sablos.sock` (default Ubuntu setup permits this).
