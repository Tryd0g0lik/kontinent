"""
content/tasks.py
"""

import os
import logging
from typing import List

from celery.worker.control import time_limit
from django.core.files.storage import default_storage
from django.db import transaction, connections
from django.db.models import F
from celery import shared_task

from content.views import fduplicate
from content.models_content_files import VideoContentModel, AudioContentModel
from project.settings import MEDIA_URL
from logs import configure_logging
from content.transactions import transaction_update, transaction_get

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


def task_process_video_upload(video_id, temp_path, file_name) -> None:
    """
    Background task for loading the video file
    """
    message = "%s: " % task_process_video_upload.__name__
    try:
        # Check the file exists
        if not os.path.exists(temp_path):
            log.info(f"Source file not found: {temp_path}")
            raise FileNotFoundError(f"Source file not found: {temp_path}")

        kwargs = {"upload_status": "processing"}
        transaction_update("content_videocontentmodel", video_id, **kwargs)
        video = transaction_get("content_videocontentmodel", video_id)
        # create basis and temporary paths.
        main_path = (
            f"{video["video_path"]}"
            if MEDIA_URL.lstrip("/") in video["video_path"]
            else "media/" + video["video_path"]
        )

        # check the duplacation
        duplicate_path = fduplicate.check_duplicate(
            file_name, model_class=VideoContentModel, field_name_list=["video_path"]
        )

        if duplicate_path:
            # If file exists we use the old file (file previously uploaded).
            kwargs_dupl = {"video_path": duplicate_path}
            transaction_update("content_videocontentmodel", video["id"], **kwargs_dupl)

            # remove the temporary file
            os.remove(temp_path) if os.path.exists(temp_path) else None
            log.info(f"Using existing file: {duplicate_path}")
        else:
            folder = main_path.split("/")[-2]
            file_name_0 = temp_path.split(temp_path.split("_")[0])[1][1:]
            file_name_1 = main_path.split(folder)[1][1:]
            main_path = (
                main_path.split(folder)[0] + f"{folder}/" + file_name_0
                if file_name_1 not in file_name_0
                else main_path
            )
            # create the basis file.
            read_bool = True
            with open(temp_path, "rb") as source:
                with open(main_path, "wb") as destination:
                    # updating the connection's state
                    while read_bool:
                        chunk = source.read(10 * 1024 * 1024)
                        if chunk:
                            destination.write(chunk)
                        else:
                            read_bool = False
            kwargs_new = {
                "video_path": MEDIA_URL.lstrip("/")
                + main_path.split(MEDIA_URL.lstrip("/"))[-1],
                "upload_status": "completed",
            }
            # Connection to the db
            transaction_update("content_videocontentmodel", video["id"], **kwargs_new)
            # new file add to the cache of file's validation
            fduplicate.add_file_hash(main_path, fduplicate.calculate_md5(main_path))

            # remove the temporary file
            os.remove(temp_path) if os.path.exists(temp_path) else None
            log.info(f"File uploaded successfully: {main_path}")

    except Exception as e:
        kwargs = {"upload_status": "failed"}
        transaction_update("content_videocontentmodel", video_id, **kwargs)
        log.error(message + f"Error processing video upload: {str(e)}")
        raise


def task_process_audio_upload(audio_id, temp_path: str, file_name: str) -> None:
    """
    Background task for loading the audio file
    """
    try:
        message = "%s: " % task_process_video_upload.__name__
        # Check the file exists
        if not os.path.exists(temp_path):
            log.info(f"Source file not found: {temp_path}")
            raise FileNotFoundError(f"Source file not found: {temp_path}")

        kwargs = {"upload_status": "processing"}
        transaction_update("content_videocontentmodel", audio_id, **kwargs)
        audio = transaction_get("content_videocontentmodel", audio_id)
        # create temporary file (in 'media/<file>')
        main_path = (
            f"{audio["video_path"]}"
            if MEDIA_URL.lstrip("/") in audio["video_path"]
            else "media/" + audio["video_path"]
        )

        # check the duplacation
        duplicate_path = fduplicate.check_duplicate(
            file_name, model_class=AudioContentModel, field_name_list=["audio_path"]
        )

        if duplicate_path:
            # If file exists we use the old file (file previously uploaded).
            kwargs_dupl = {"video_path": duplicate_path}
            transaction_update("content_audiocontentmodel", audio["id"], **kwargs_dupl)

            # Removing temporary file
            os.remove(temp_path) if os.path.exists(temp_path) else None
            log.info(f"Using existing audio file: {duplicate_path}")
        else:
            folder = main_path.split("/")[-2]
            file_name_0 = temp_path.split(temp_path.split("_")[0])[1][1:]
            file_name_1 = main_path.split(folder)[1][1:]
            main_path = (
                main_path.split(folder)[0] + f"{folder}/" + file_name_0
                if file_name_1 not in file_name_0
                else main_path
            )
            # Create the basis file
            with open(temp_path, "rb") as source:
                with open(main_path, "wb") as destination:
                    # updating the connection's state
                    while read_bool:
                        chunk = source.read(10 * 1024 * 1024)
                        if chunk:
                            destination.write(chunk)
                        else:
                            read_bool = False

            kwargs_new = {
                "audio_path": MEDIA_URL.lstrip("/")
                + main_path.split(MEDIA_URL.lstrip("/"))[-1],
                "upload_status": "completed",
            }
            # Connection to the db
            transaction_update("content_audiocontentmodel", audio["id"], **kwargs_new)

            # Adding the server's path of file to the cash of the file's validator
            fduplicate.add_file_hash(main_path, fduplicate.calculate_md5(main_path))

            # REmoving the temporary file (from 'media/<file>')
            default_storage.delete(temp_path)
            log.info(f"Audio file uploaded successfully: {main_path}")

    except Exception as e:
        kwargs = {"upload_status": "failed"}
        transaction_update("content_audiocontentmodel", audio_id, **kwargs)
        log.error(message + f"Error processing audio upload: {str(e)}")
        raise
