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
- Start Command:
  - `gunicorn -c gunicorn.conf.py medicine_qr_app.wsgi:application`
- Build/Run Commands:
  - PreStart (Install deps): `python -m pip install -r requirements.txt`
  - PostBuild or PreStart (Static): `python manage.py collectstatic --noinput`
  - PreStart (Migrations): `python manage.py migrate --noinput`
- Port: Leave unset. Coolify injects `PORT`; Gunicorn reads it via `gunicorn.conf.py`.
- Health Check: Path `/` or add `/healthz` (optional).

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
$env:PORT="9000"; waitress-serve --port %PORT% --host 0.0.0.0 medicine_qr_app.wsgi:application

# On Linux/macOS, you can use Gunicorn:
# $env:PORT="9000"; gunicorn -c gunicorn.conf.py medicine_qr_app.wsgi:application
```

## Notes
- No hardcoded port anywhere; Coolify’s `PORT` is used automatically.
- WhiteNoise serves static files efficiently; `collectstatic` must be run before starting.
- For managed DBs, prefer Coolify’s Postgres service and set `DATABASE_URL` accordingly.

## Optional: Health Endpoint
You can add a lightweight health route for better checks:
- URL: `/healthz`
- Returns HTTP 200 with a simple JSON `{"status":"ok"}`.

Let me know if you want me to scaffold the `/healthz` view and route.
