from django.apps import AppConfig
from django.contrib.staticfiles.storage import StaticFilesStorage


class CustomStaticFilesStorage(StaticFilesStorage):
    def stored_name(self, name):
        return name

class ContentConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "content"
