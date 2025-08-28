import os

from celery import Celery
from celery.schedules import crontab

from project import celeryconfig


# Set the default Django settings module for the 'celery' program.
# Celery, It's for cache of db.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

app = Celery(
    "proj",
    include=[
        "content.tasks",
    ],
)
app.config_from_object(celeryconfig)
