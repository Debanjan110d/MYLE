import os

# Simple, environment-driven Gunicorn config for Coolify
# Do not hardcode port or advanced settings; keep minimal.

# Bind only if PORT is provided by the platform
_port = os.getenv('PORT')
if _port:
    bind = f"0.0.0.0:{_port}"

# Optionally respect WEB_CONCURRENCY if provided; otherwise let Gunicorn default
web_concurrency = os.getenv("WEB_CONCURRENCY")
if web_concurrency:
	workers = int(web_concurrency)

# Rely on Gunicorn defaults for other settings to keep it simple
accesslog = "-"
errorlog = "-"
