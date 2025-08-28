import logging
from typing import List

from django.db import transaction
from django.db.models import F
from celery import shared_task

from content.models_content_files import VideoContentModel, AudioContentModel
from logs import configure_logging
from project.settings import CONTENT_TYPES_CHOICES

log = logging.getLogger(__name__)
configure_logging(logging.INFO)


@shared_task(
    name=__name__,
    bind=False,
    authretry_for=(TimeoutError,),
)
def increment_content_counter(data_numbers_list: List[dict]) -> None:
    # contents_views: list = [VideoContentModel, AudioContentModel]
    message = "%s: " % increment_content_counter.__name__

    def handler_of_counter_by_index(view: dict):
        if view.__getitem__("content_type").lower() == "video":
            VideoContentModel.objects.filter(
                id=view.__getitem__("id"),
                content_type=view.__getitem__("content_type"),
            ).update(counter=F("counter") + 1)

        if view.__getitem__("content_type").lower() == "audio":
            AudioContentModel.objects.filter(
                id=view.__getitem__("id"),
                content_type=view.__getitem__("content_type"),
            ).update(counter=F("counter") + 1)

    try:
        with transaction.atomic():
            for content_ids in data_numbers_list:
                # This log don't touch!
                log.info(
                    message
                    + "'content_ids' Type: %s Len: %s Total len: %s"
                    % (
                        type(content_ids),
                        (
                            content_ids.__dict__
                            if isinstance(content_ids, dict)
                            else f"--XXX'content_ids'--{str(content_ids)}"
                        ),
                        len(data_numbers_list),
                    )
                )

                result = [
                    (
                        handler_of_counter_by_index(content_ids)
                        if isinstance(content_ids, dict)
                        else [
                            (
                                handler_of_counter_by_index(content_id)
                                if isinstance(content_id, dict)
                                else [
                                    handler_of_counter_by_index(v) for v in content_id
                                ]
                            )
                            for content_id in content_ids
                        ]
                    )
                ]
                log.info(message + f"RESULT: {str(result)}")
        return
    except Exception as error:
        log.error(message + f"Error => {error.args[0]}")
        print(message + error.args[0])
        return
