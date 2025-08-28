import logging
from typing import List

from django.db import transaction
from django.db.models import F
from celery import shared_task

from content.models_content_files import VideoContentModel, AudioContentModel
from logs import configure_logging

log = logging.getLogger(__name__)
configure_logging(logging.INFO)


@shared_task(
    name=__name__,
    bind=True,
    authretry_for=(TimeoutError,),
)
def increment_content_counter(data_numbers_list: List[dict]) -> None:
    message = "%s: Error => " % increment_content_counter.__name__
    try:
        with transaction.atomic():
            for content_ids in data_numbers_list:
                if isinstance(content_ids, dict):
                    if content_ids.__getitem__("video"):
                        VideoContentModel.objects.filter(
                            id__in=content_ids["id"]
                        ).update(counter=F("count") + 1)
                    if content_ids.__getitem__("audio"):
                        AudioContentModel.objects.filter(
                            id__in=content_ids["id"]
                        ).update(counter=F("counter") + 1)
                else:
                    print(message + "Something what wrong!")
                    raise ValueError(message + "Something what wrong!")
        return
    except Exception as error:
        log.error(message + error.args[0])
        print(message + error.args[0])
        return
