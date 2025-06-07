import os

PORT = int(os.environ.get("PORT", "8000"))
GUNICORN_WORKERS = int(os.environ.get("GUNICORN_WORKERS", "2"))
GUNICORN_THREADS = int(os.environ.get("GUNICORN_THREADS", "4"))

bind = f":{PORT}"
workers = GUNICORN_WORKERS
threads = GUNICORN_THREADS
worker_class = "uvicorn.workers.UvicornWorker"

"""
Equivalent command
gunicorn --bind=:8000 --workers=2 --threads=4 \
    --worker-class=uvicorn.workers.UvicornWorker app.main:app
"""
