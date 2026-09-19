# Deployment Guide

This system is **single-tenant**: one deployment and one database per
client business. Do not point two clients at the same database — see
`SECURITY.md` and the README for why multi-tenancy isn't supported yet.

This guide covers a standard Ubuntu VPS deployment (gunicorn + nginx +
systemd + Postgres + Let's Encrypt), which is the recommended setup for
selling this to clients. A PaaS alternative (Render/Railway) is noted at
the end for getting a first client live faster with less setup.

---

## Prerequisites

- A VPS running Ubuntu 22.04+ (DigitalOcean, Hetzner, Linode, AWS Lightsail — any is fine)
- A domain or subdomain pointed at the server's IP (an A record)
- SSH access to the server

## 1. Server setup

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-venv python3-pip postgresql postgresql-contrib nginx git
```

## 2. Database

```bash
sudo -u postgres psql
```
```sql
CREATE DATABASE client_dms;
CREATE USER client_dms_user WITH PASSWORD 'choose-a-strong-random-password';
GRANT ALL PRIVILEGES ON DATABASE client_dms TO client_dms_user;
\q
```

## 3. Deploy the code

```bash
sudo mkdir -p /opt/dms
sudo chown $USER:$USER /opt/dms
cd /opt/dms
# copy your project here (git clone, scp, or rsync — whatever you use)

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

## 4. Environment

Create `/opt/dms/.env`:

```
DATABASE_URL=postgresql://client_dms_user:choose-a-strong-random-password@localhost:5432/client_dms
SECRET_KEY=<generate with: python3 -c "import secrets; print(secrets.token_hex(32))">
FLASK_APP=wsgi.py
FLASK_DEBUG=0
```

**Never reuse a `SECRET_KEY` across clients or copy it from development.**
Generate a fresh one per deployment.

## 5. Initialize the database

```bash
export FLASK_APP=wsgi.py
flask db upgrade
python seed.py
```

This creates the default `admin` / `admin123` login — **change this
password immediately** (via the app, once it's running) before handing
the system to the client.

## 6. Run with gunicorn (test first)

```bash
gunicorn -w 3 -b 127.0.0.1:8000 wsgi:app
```

Visit `http://<server-ip>:8000` briefly to confirm it works, then Ctrl+C
and move on to running it as a proper service.

## 7. systemd service (keeps it running, auto-restarts)

Create `/etc/systemd/system/dms.service`:

```ini
[Unit]
Description=Ledger DMS (gunicorn)
After=network.target postgresql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/dms
EnvironmentFile=/opt/dms/.env
ExecStart=/opt/dms/venv/bin/gunicorn -w 3 -b 127.0.0.1:8000 wsgi:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo chown -R www-data:www-data /opt/dms
sudo systemctl daemon-reload
sudo systemctl enable dms
sudo systemctl start dms
sudo systemctl status dms   # confirm it's active (running)
```

## 8. nginx reverse proxy

Create `/etc/nginx/sites-available/dms`:

```nginx
server {
    listen 80;
    server_name client.yourdomain.com;

    location /static/ {
        alias /opt/dms/app/static/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/dms /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 9. HTTPS (Let's Encrypt, free)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d client.yourdomain.com
```

Certbot edits the nginx config to redirect HTTP → HTTPS and sets up
auto-renewal. Confirm renewal works with `sudo certbot renew --dry-run`.

## 10. Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

Postgres should **not** be reachable from outside the server — by default
it only listens on localhost, which is correct; don't change that unless
you have a specific reason to.

## 11. Automated backups

Add a daily cron job that hits the backup route (or calls the underlying
Python function directly). Simplest version using the app itself:

```bash
crontab -e
```
```cron
0 2 * * * curl -s -X POST -b "session=<a long-lived admin session cookie>" https://client.yourdomain.com/backup/create
```

A cleaner approach is a small standalone script that calls
`app.backup_engine.dump_all()` directly and writes the file, run via cron
— this avoids needing a session cookie at all. Either way: **copy the
resulting backup files off the server periodically** (e.g. to S3, or
`rsync` to another machine) — a backup that lives only on the server it's
backing up doesn't protect you if that server is lost.

## 12. Handing off to the client

- Change the default admin password before sharing access
- Create their real user accounts via **Users** with appropriate
  permissions (don't just give everyone the admin login)
- Fill in **Settings → Business** with their real business name, address,
  and contact info (this appears on printed invoices)
- Do one full walkthrough with them: add a product, record a purchase, a
  sale, and show them the dashboard update live

## Updating a deployed client later

```bash
cd /opt/dms
sudo systemctl stop dms
source venv/bin/activate
git pull            # or however you deliver updated code
pip install -r requirements.txt
flask db upgrade
sudo systemctl start dms
```

Always run `flask db upgrade` after pulling new code — new phases have
historically included database migrations, and skipping this step is the
most common cause of "column does not exist" errors after an update.

---

## Alternative: PaaS (faster to launch, less control)

For a first client or a quick demo, **Render** or **Railway** let you skip
steps 1–10 entirely:

1. Push the code to a GitHub repo
2. Create a new Web Service, point it at the repo
3. Add a managed Postgres database (both platforms offer one)
4. Set environment variables (`DATABASE_URL` from their Postgres add-on,
   `SECRET_KEY`, `FLASK_APP=wsgi.py`, `FLASK_DEBUG=0`)
5. Set the start command to `gunicorn wsgi:app`
6. Run `flask db upgrade` and `python seed.py` via their one-off
   shell/console feature

HTTPS and the reverse proxy are handled for you. This costs more per
client at scale than a single VPS running several clients, but gets you
live in minutes rather than an hour.
