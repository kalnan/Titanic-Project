"""Gunicorn configuration for running the FastAPI app with uvicorn workers."""
import multiprocessing
import os

bind = f"0.0.0.0:{os.getenv('PORT', 8000)}"
worker_class = "uvicorn.workers.UvicornWorker"
workers = int(os.getenv("WEB_CONCURRENCY", min(multiprocessing.cpu_count() * 2 + 1, 4)))
timeout = int(os.getenv("GUNICORN_TIMEOUT", 120))
keepalive = 5
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")
