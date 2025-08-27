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
        "person.tasks.task_user_is_authenticate",
        "person.tasks.task_cache_hew_user",
        "person.tasks.task_user_is_login",
        "person.tasks.task_user_from_cache_to_td_repeat",
    ],
)
app.config_from_object(celeryconfig)

# https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html#introduction
app.conf.beat_schedule = {
    "midnigth-tast": {
        "task": "person.tasks.task_user_from_cache_to_td_repeat.task_user_from_cache",
        "schedule": crontab(hour=1, minute=0),
    }
}
