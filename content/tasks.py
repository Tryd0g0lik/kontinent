"""
content/tasks.py
"""

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
    bind=False,
    authretry_for=(TimeoutError,),
)
def increment_content_counter(data_numbers_list: List[dict]) -> None:
    """
    The whole difficulty is that we get both pagination-based page lists and a single page - from the database and
     from the cache. Therefore, the structure is slightly different
    :param data_numbers_list:
    :return:
    """
    contents_views: list = [VideoContentModel.objects, AudioContentModel.objects]
    list_of_content_names: List[str] = ["audio", "video"]
    message = "%s: " % increment_content_counter.__name__

    def handler_of_counters_of_models(
        view: dict, model_list: list, list_content_name: List[str]
    ) -> None:
        for one_model in model_list:
            for content_name in list_content_name:
                if view.__getitem__("content_type").lower() == content_name:
                    one_model.filter(
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
                        handler_of_counters_of_models(
                            content_ids, contents_views, list_of_content_names
                        )
                        if isinstance(content_ids, dict)
                        else [
                            (
                                handler_of_counters_of_models(
                                    content_id, contents_views, list_of_content_names
                                )
                                if isinstance(content_id, dict)
                                else [
                                    handler_of_counters_of_models(
                                        v, contents_views, list_of_content_names
                                    )
                                    for v in content_id
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
