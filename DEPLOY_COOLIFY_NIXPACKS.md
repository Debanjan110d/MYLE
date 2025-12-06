# Deploying MYLE Django App on Coolify with Nixpacks

This guide configures your Django app for production on Coolify using Nixpacks. It avoids hardcoded ports and uses environment-driven Gunicorn.

## Prerequisites
- A Coolify instance (with domain/SSL set up).
- Access to your Git repo (branch `main`).
- Required env vars prepared (see below).

## Codebase Summary
- `gunicorn.conf.py`: Binds only when `PORT` is present; respects `WEB_CONCURRENCY`; minimal logs.
- `medicine_qr_app/wsgi.py`: Wraps Django WSGI with WhiteNoise to serve static files from `STATIC_ROOT`.
- `medicine_qr_app/settings.py`: Reads settings from environment (`DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DATABASE_URL`). Uses WhiteNoise and `STATIC_ROOT`.
- `requirements.txt`: Includes Django, Gunicorn, WhiteNoise, `dj-database-url`.

## Coolify Service Setup (Nixpacks)
- Create Service: Choose Nixpacks → Python.
- Repository: Connect this repo (`main` branch).
- Domains: Set your domain (e.g., `http://djangot.172.61.226.153.sslip.io`). Enable HTTPS later.

### Build Section
- Install Command: leave empty (recommended). Nixpacks will run pip in its venv.
  - If you must set it, use: `/opt/venv/bin/pip install -r requirements.txt`
- Build Command: leave empty (Nixpacks detects Python project automatically)
- Base Directory: `/`
- Publish Directory: `/` (or leave empty)
- Custom Docker Options: leave empty

### Start Command
  - Type it manually; avoid pasting from Markdown (links can inject `[ ... ](...)` and break the command).
  - Port is not set here; Coolify injects `PORT`, which Gunicorn reads from `gunicorn.conf.py`.

 Pre-deployment: `python manage.py migrate --noinput`
 Post-deployment: optional `python manage.py collectstatic --noinput`
 Tip: type commands by hand so they stay plain text (no `[manage.py](...)` references).
- Post-deployment: optional `python manage.py collectstatic --noinput` if not already run at build time

### Health Check
- HTTP path: `/healthz`
- Method: GET
- Interval: 30s; Timeout: 5s; Healthy threshold: 2

## Environment Variables
- `DJANGO_SECRET_KEY`: Strong unique value (required).
- `DJANGO_DEBUG`: `false` (production).
- `DJANGO_ALLOWED_HOSTS`: e.g., `example.com,www.example.com` (required in production).
- `WEB_CONCURRENCY`: Optional (e.g., `2` or `3`).
- Database:
  - SQLite: No `DATABASE_URL`. Add a volume for `db.sqlite3`.
  - Postgres/MySQL: Set `DATABASE_URL` (e.g., `postgres://user:pass@host:5432/db`).

## Volumes (SQLite)
- Map a Coolify volume to `/app/db.sqlite3` to persist data.
- Optional: Map `/app/staticfiles` if you want static persistence between builds.

## Local Test (PowerShell)
Use these commands to verify behavior locally.

```powershell
# Activate venv if you have one
& d:/MYLE/.venv/Scripts/Activate.ps1

# Install dependencies
python -m pip install -r requirements.txt

# Prepare assets and DB
python manage.py collectstatic --noinput
python manage.py migrate --noinput

# On Windows, Gunicorn isn't supported (missing fcntl). Use Waitress:
python -m pip install waitress
$env:PORT="9000"; waitress-serve --port $env:PORT --host 0.0.0.0 medicine_qr_app.wsgi:application

# On Linux/macOS, you can use Gunicorn:
# PORT=9000 gunicorn -c gunicorn.conf.py medicine_qr_app.wsgi:application
```

## Notes
- No hardcoded port anywhere; Coolify’s `PORT` is used automatically.
- WhiteNoise serves static files efficiently; `collectstatic` must be run before starting.
- For managed DBs, prefer Coolify’s Postgres service and set `DATABASE_URL` accordingly.

### Troubleshooting
- Error: `/root/.nix-profile/bin/python: No module named pip`
  - Cause: Overriding Install Command to `python -m pip ...` bypasses Nixpacks' venv.
  - Fix: Clear the Install Command, or set it to `/opt/venv/bin/pip install -r requirements.txt`.

## Optional: Health Endpoint
You can add a lightweight health route for better checks:
- URL: `/healthz`
- Returns HTTP 200 with a simple JSON `{"status":"ok"}`.

Let me know if you want me to scaffold the `/healthz` view and route.
