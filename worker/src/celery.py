from celery import Celery

from src import config

# Main Celery app
celeryapp = Celery("hello", broker=config.CELERY_BACKEND)
