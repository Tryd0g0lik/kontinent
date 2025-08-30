"""
content/tasks.py
"""

import logging
import os
from typing import List

from django.core.files.storage import default_storage
from django.db import transaction, connections
from django.db.models import F
from celery import shared_task
from dulwich.porcelain import remove

from content.views import fduplicate


from content.file_validator import FileDuplicateChecker
from content.models_content_files import VideoContentModel, AudioContentModel
from logs import configure_logging
from project import settings
from project.settings import MEDIA_PATH_TEMPLATE_AUDIO

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


@shared_task
def task_process_video_upload(video_id, file_data, file_name):
    """
    Фоновая задача для обработки загрузки видео файла
    """

    message = "%s: " % task_process_video_upload.__name__
    try:
        video = VideoContentModel.objects.get(id=video_id)
        video.upload_status = "processing"
        video.asave()
        # Сохраняем файл во временное место
        main_path = f"media/{video.video_path.name}"
        temp_path = f'media/{file_name.split("/video/")[-1]}'
        with open(temp_path, "wb") as f:
            f.write(file_data)

        # Проверяем дубликаты
        duplicate_path = fduplicate.check_duplicate(
            video, model_class=VideoContentModel, field_name_list=["video_path"]
        )

        if duplicate_path:
            # Если файл уже существует, используем существующий
            with transaction.atomic():
                # Connection to the db
                with connections["default"].cursor() as cursor:
                    try:
                        # SQL
                        cursor.execute(
                            """
                            UPDATE content_videocontentmodel SET video_path = "%s" WHERE id = %i;
                            """
                            % (duplicate_path, video.__getattribute__("id"))
                        )

                    except Exception as error:
                        log.info(message + f"ERROR => {error.args[0]}")
                    finally:
                        cursor.close()

            # video.video_path = duplicate_path
            # video.upload_status = "completed"
            # video.asave()
            # # Удаляем временный файл
            os.remove(temp_path)
            log.info(f"Using existing file: {duplicate_path}")
        else:
            # Сохраняем файл в постоянное место

            with open(temp_path, "rb") as source:
                with open(main_path, "wb") as destination:
                    destination.write(source.read())

            video.video_path = main_path.split("media/")[-1]
            video.upload_status = "completed"
            video.asave()

            # Добавляем файл в кэш валидатора
            fduplicate.add_file_hash(main_path, fduplicate.calculate_md5(main_path))

            # Удаляем временный файл
            os.remove(temp_path)
            log.info(f"File uploaded successfully: {main_path}")

    except Exception as e:
        log.error(f"Error processing video upload: {str(e)}")
        raise


@shared_task
def task_process_audio_upload(audio_id, file_data, file_name):
    """
    Фоновая задача для обработки загрузки аудио файла
    """
    try:
        audio = AudioContentModel.objects.get(id=audio_id)
        audio.upload_status = "processing"
        audio.asave()
        # Сохраняем файл во временное место
        main_path = f"media/{audio.audio_path.name}"
        temp_path = f'media/{file_name.split("/video/")[-1]}'
        with open(temp_path, "wb") as f:
            f.write(file_data)

        # Проверяем дубликаты
        duplicate_path = fduplicate.check_duplicate(
            audio, model_class=AudioContentModel, field_name_list=["audio_path"]
        )

        if duplicate_path:
            # Если файл уже существует, используем существующий
            audio.audio_path = duplicate_path
            audio.upload_status = "completed"
            audio.asave()
            # Удаляем временный файл
            os, remove(temp_path)
            log.info(f"Using existing audio file: {duplicate_path}")
        else:
            # Сохраняем файл в постоянное место

            with open(temp_path, "rb") as source:
                with open(main_path, "wb") as destination:
                    destination.write(source.read())

            audio.video_path = main_path.split("media/")[-1]
            audio.upload_status = "completed"
            audio.asave()

            # Добавляем файл в кэш валидатора
            fduplicate.add_file_hash(main_path, fduplicate.calculate_md5(main_path))

            # Удаляем временный файл
            default_storage.delete(temp_path)
            log.info(f"Audio file uploaded successfully: {main_path}")

    except Exception as e:
        log.error(f"Error processing audio upload: {str(e)}")
        raise


@shared_task
def task_cleaning_media_root(path: str):
    os.remove(path) if os.path.exists(path) else None
