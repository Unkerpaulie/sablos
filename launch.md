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
5. Once it boots, point your DNS at the droplet IP (A record for
   `sablos.devs.tt`).

## 2. Initial server hardening (as `root`)

> Skip any step you've already done — this droplet already has `certbot`,
> a `sablos` user, and an nginx site for `sablos.devs.tt`.

SSH in: `ssh root@<droplet-ip>`

```bash
# Patch the box
apt update && apt upgrade -y

# Create the application user (skip if `sablos` already exists)
adduser --disabled-password --gecos "" sablos
usermod -aG sudo sablos
mkdir -p /home/sablos/.ssh
cp ~/.ssh/authorized_keys /home/sablos/.ssh/
chown -R sablos:sablos /home/sablos/.ssh
chmod 700 /home/sablos/.ssh
chmod 600 /home/sablos/.ssh/authorized_keys

# Firewall — only SSH and HTTP/HTTPS
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

# System packages (skip any already present)
apt install -y python3-venv python3-pip git nginx certbot python3-certbot-nginx
```

Optional but recommended: edit `/etc/ssh/sshd_config` to set
`PermitRootLogin no` and `PasswordAuthentication no`, then
`systemctl restart ssh`. From here on, log in as `sablos`.

## 3. Clone the repo into `/var/www/sablos_root`

The repo lives under `/var/www` so nginx (`www-data`) can read static
files without traversing a user home directory. The `sablos` user owns
the tree.

```bash
ssh sablos@<droplet-ip>
sudo mkdir -p /var/www
sudo chown sablos:sablos /var/www
cd /var/www
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

## 7. Wire up nginx for `sablos.devs.tt`

Static files are served by **WhiteNoise** inside the gunicorn process,
so nginx only needs to proxy and (optionally) serve `/media/` directly.
There is no `location /static/` block.

If you already have an nginx site for `sablos.devs.tt` (created when you
ran `certbot --nginx` earlier for another project), **don't replace it**.
Instead, copy the `location /media/` and `location /` blocks from
`deploy/sablos.nginx.conf` into the existing `server { ... }` block(s)
for `sablos.devs.tt`, and **remove any old `location /static/` block**
that points at a stale path. Then:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

Otherwise, install fresh:

```bash
sudo cp deploy/sablos.nginx.conf /etc/nginx/sites-available/sablos
sudo ln -sf /etc/nginx/sites-available/sablos /etc/nginx/sites-enabled/sablos
sudo nginx -t
sudo systemctl reload nginx
```

Create the media directory if it doesn't exist:

```bash
sudo mkdir -p /var/www/sablos_root/media
sudo chown sablos:sablos /var/www/sablos_root/media
```

Visit `http://sablos.devs.tt` — the site should load with styling intact.

## 8. TLS via Let's Encrypt

If `sablos.devs.tt` already has a certificate (you mentioned certbot is
already on this box), skip to step 9. Otherwise:

```bash
sudo certbot --nginx -d sablos.devs.tt
```

Certbot rewrites the nginx config to add the TLS server block and a
HTTP→HTTPS redirect. The cert auto-renews via the systemd timer
(`systemctl list-timers | grep certbot` to confirm).

Because `DJANGO_SECURE_SSL_REDIRECT=true` is set in `.env`, Django will
also enforce HTTPS at the application layer.

## 9. Verify

- `https://sablos.devs.tt/` — public homepage.
- `https://sablos.devs.tt/say-hi/` — contact form.
- `https://sablos.devs.tt/login/` — staff login.
- `https://sablos.devs.tt/wip/` — dashboard (requires login).
- `https://sablos.devs.tt/admin/` — Django admin.

## 10. Day-to-day redeploys

After committing and pushing changes:

```bash
ssh sablos@<droplet-ip>
cd /var/www/sablos_root
./redeploy.sh
```

`redeploy.sh` snapshots `db.sqlite3` into `backups/`, pulls the latest
code, installs new dependencies, runs migrations, collects static, and
restarts the gunicorn service. Use `SKIP_MIGRATE=1 ./redeploy.sh` for
template-only changes.

The `sudo systemctl restart sablos` line at the end of `redeploy.sh`
will prompt for your password unless you give the `sablos` user a
passwordless sudoers rule scoped to that one command, e.g. drop this
into `/etc/sudoers.d/sablos-systemctl` (via `sudo visudo -f`):

```
sablos ALL=(root) NOPASSWD: /bin/systemctl restart sablos, /bin/systemctl status sablos
```

## 11. Backups

The SQLite database is a single file, `db.sqlite3`. The simplest backup
is a periodic copy off the droplet, e.g. via cron:

```bash
crontab -e
# 03:30 every day, copy the DB file with a timestamp
30 3 * * * cp /var/www/sablos_root/db.sqlite3 /home/sablos/backups/db.sqlite3.$(date +\%F)
```

For off-box durability, configure Digital Ocean weekly droplet backups
(extra ~$1.20/mo) or rsync `/var/www/sablos_root/db.sqlite3` to
S3-compatible storage from cron.

## Troubleshooting

- **502 Bad Gateway**: gunicorn isn't running. `sudo systemctl status sablos` and `journalctl -u sablos`.
- **CSRF / DisallowedHost errors**: check `DJANGO_ALLOWED_HOSTS` in `.env` matches the URL you're using.
- **Static files missing or unstyled CSS**: re-run `./redeploy.sh` (which calls `collectstatic`). Static files are served by WhiteNoise from `STATIC_ROOT` (`<repo>/staticfiles/`); if you still see a stale `location /static/` block in the nginx site pointing at a path that doesn't exist, delete it and `sudo systemctl reload nginx`.
- **Permission denied on socket**: confirm the `RuntimeDirectory=sablos` line in the service file and that nginx's `www-data` user is in a position to reach `/run/sablos/sablos.sock` (default Ubuntu setup permits this).
