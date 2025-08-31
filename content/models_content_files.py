"""
content/models_content_files.py
"""

import asyncio
import os
import threading
import uuid
import logging
from datetime import datetime

from django.db import models, connections, transaction
from django.core import validators
from django.utils.translation import gettext_lazy as _
from content.models import ContentFileBaseModel
from content.transactions import transaction_update
from logs import configure_logging

from project.settings import (
    MEDIA_PATH_TEMPLATE_AUDIO,
    MEDIA_PATH_TEMPLATE_VIDEO,
    MEDIA_URL,
)

log = logging.getLogger(__name__)
configure_logging(logging.INFO)


def loop_upload(tusk_func, **kwargs):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(asyncio.to_thread(tusk_func, **kwargs))


def generate_filepath(instance, filename):
    from pathlib import Path
    from project.settings import MEDIA_ROOT

    # from content.tasks import task_cleaning_media_root

    olp_mkdr = MEDIA_ROOT.strip()
    path_iter = (p for p in instance.split("/"))
    while path_iter:
        path_iter_next = next(path_iter)
        (
            None
            if os.path.exists(f"{olp_mkdr}/{path_iter_next}")
            else Path(olp_mkdr + "\\" + path_iter_next).mkdir()
        )
        path_iter = False if len(path_iter_next) == 0 else path_iter
        olp_mkdr += "\\" + path_iter_next


class VideoContentModel(ContentFileBaseModel):
    """
    Video Content Model
    """

    video_path = models.FileField(
        upload_to=MEDIA_PATH_TEMPLATE_VIDEO,
        help_text=_("Пример: 'media/2025/07/12/video/your-file.mp4'"),
        blank=True,
        null=True,
    )
    video_url = models.URLField(
        verbose_name=_("Video URL"),
        help_text=_("Указать URL на файл"),
        validators=[
            validators.RegexValidator(
                regex=r"(^https?:\/\/[a-z0-9-\/_]+\.(ru|com|net)\/[a-z0-9-\/_]+\.[a-z4]{2,4})",
                message=_("Enter valid URL!"),
            )
        ],
        null=True,
        blank=True,
    )
    subtitles_url = models.URLField(
        blank=True,
        null=True,
        verbose_name=_("Subtitles URL"),
        help_text=_("Указать URL на файл"),
        validators=[
            validators.RegexValidator(
                regex=r"(^https?:\/\/[a-z0-9-\/_]+\.(ru|com|net)\/[a-z0-9-\/_]+\.[a-z4]{2,4})",
                message=_("Enter valid URL!"),
            )
        ],
    )
    upload_status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("processing", "Processing"),
            ("completed", "Completed"),
            ("failed", "Failed"),
        ],
        default="pending",
        editable=False,
    )

    def save(self, *args, **kwargs) -> None:
        """
        Here is we only getting the line on db.
        Note: This metho don't saving a file to the server. \
        Tasks of Celery do saving files at server side
        :param args:
        :param kwargs:
        :return:
        """
        from content.tasks import task_process_video_upload

        self.content_type = "video"

        # If we have new file for upload
        if hasattr(self, "_video_file") and self.upload_status != "completed":
            self.upload_status = "processing"

            # TASK
            file_data = self._video_file.read()
            file_name = f"{uuid.uuid4()}_{self._video_file.name}"
            super().save(*args, **kwargs)
            kwargs_video = {
                "video_id": self.id,
                "file_data": file_data,
                "file_name": file_name,
            }

            threading.Thread(
                target=loop_upload,
                args=(task_process_video_upload,),
                kwargs=kwargs_video,
            ).start()
        if hasattr(self, "video_path") and self.upload_status != "completed":
            self.upload_status = "processing"
            self.set_video_file(self.video_path)

            # TASK
            video_title = self._video_file.name.split("/")[-1]
            file_name = f"{self._video_file.name}".replace(
                video_title, f"{uuid.uuid4()}_{video_title}"
            )
            if not self.id:
                file_path = self.video_path.name if self.video_path else None
                # Disconnection the field of file
                old_video_path = None
                if self.video_path:
                    old_video_path = self.video_path
                    self.video_path = None
                with transaction.atomic():
                    try:
                        # Records thi line in db
                        super().save(*args, **kwargs)
                        if old_video_path:
                            # Records the field 'video_path' without saving of file to the server
                            self.video_path = old_video_path
                            path_template = (
                                f"{datetime.now().strftime("%Y/%m/%d/")}video/"
                            )
                            generate_filepath(path_template, self.video_path.name)
                            self.__class__.objects.filter(pk=self.pk).update(
                                video_path=MEDIA_URL.lstrip("/")
                                + path_template
                                + file_path
                            )
                    except Exception as error:
                        log.error(
                            "%s: ERROR => %s",
                            (
                                VideoContentModel.__class__.__name__
                                + "."
                                + self.save.__name__,
                                error,
                            ),
                        )

            else:
                kwargs_audio = {
                    "title": self.title,
                    "counter": self.counter,
                    "order": self.order,
                    "content_type": self.content_type,
                    "video_url": self.video_url,
                    "subtitles_url": self.subtitles_url,
                    "video_path": self.video_path,
                    "is_active": self.is_active,
                    "upload_status": self.upload_status,
                }
                transaction_update("content_videocontentmodel", self.id, **kwargs_audio)

            # Temporary file
            temp_path = f'{MEDIA_URL.lstrip("/")}{file_name.split("/video/")[-1]}'
            kwargs_video = {
                "video_id": self.id,
                "temp_path": temp_path,
                "file_name": file_name,
            }
            # create the temporary file
            read_bool = True
            with open(temp_path, "wb") as f:
                while read_bool:
                    chunk = self._video_file.read(10 * 1024 * 1024)
                    if chunk:
                        f.write(chunk)
                    else:
                        read_bool = False

            threading.Thread(target=loop_upload, kwargs=kwargs_video).start()

    def set_video_file(self, file):
        """Method for sending a file to the initial file's processing"""

        self._video_file = file

    class Meta:
        verbose_name = _("Video Content")
        verbose_name_plural = _("Video Contents")


class AudioContentModel(ContentFileBaseModel):
    """
    Audio Content Model
    """

    audio_path = models.FileField(
        upload_to=MEDIA_PATH_TEMPLATE_AUDIO,
        help_text=_("Пример: 'your-file.mp3'"),
        blank=True,
        null=True,
        validators=[
            validators.RegexValidator(
                regex=r"(^[a-z][a-z0-9-\/_]+\/{0,1}[a-z0-9-\/_]?\.[a-z2-4]{2,4})",
                message=_("Enter valid pathname!"),
            )
        ],
    )
    audio_url = models.URLField(
        verbose_name=_("Audio URL"),
        help_text=_("Pathname to the audio file"),
        validators=[
            validators.RegexValidator(
                regex=r"(^https?:\/\/[a-z0-9-\/_]+\.(ru|com|net)\/[a-z0-9-\/_]+\.[a-z2-4]{2,4})",
                message=_("Enter valid URL!"),
            )
        ],
        null=True,
        blank=True,
    )
    text = models.TextField(
        verbose_name=_("Text"),
        help_text=_("This is the audio content"),
    )
    # Поле для отслеживания статуса загрузки
    upload_status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("processing", "Processing"),
            ("completed", "Completed"),
            ("failed", "Failed"),
        ],
        default="pending",
        editable=False,
    )

    def save(self, *args, **kwargs) -> None:
        """
        Here is we only getting the line on db.
        Note: This metho don't saving a file to the server. \
        Tasks of Celery do saving files at server side
        :param args:
        :param kwargs:
        :return:
        """
        from content.tasks import task_process_audio_upload

        self.content_type = "video"

        # If we have new file for upload
        if hasattr(self, "_audio_file") and self.upload_status != "completed":
            self.upload_status = "processing"

            # TASK
            file_data = self._audio_file.read()
            file_name = f"{uuid.uuid4()}_{self._audio_file.name}"
            super().save(*args, **kwargs)
            kwargs_audio = {
                "video_id": self.id,
                "file_data": file_data,
                "file_name": file_name,
            }

            threading.Thread(
                target=loop_upload,
                args=(task_process_audio_upload,),
                kwargs=kwargs_audio,
            ).start()
        if hasattr(self, "audio_path") and self.upload_status != "completed":
            self.upload_status = "processing"
            self.set_audio_file(self.audio_path)

            # TASK
            video_title = self._audio_file.name.split("/")[-1]
            file_name = f"{self._audio_file.name}".replace(
                video_title, f"{uuid.uuid4()}_{video_title}"
            )
            if not self.id:
                file_path = self.audio_path.name if self.audio_path else None
                # Disconnection the field of file
                old_audio_path = None
                if self.audio_path:
                    old_audio_path = self.audio_path
                    self.audio_path = None
                with transaction.atomic():
                    try:
                        # Records thi line in db
                        super().save(*args, **kwargs)
                        if old_audio_path:
                            # Records the field 'audio_path' without saving of file to the server
                            self.audio_path = old_audio_path
                            path_template = (
                                f"{datetime.now().strftime("%Y/%m/%d/")}video/"
                            )
                            generate_filepath(path_template, self.audio_path.name)
                            self.__class__.objects.filter(pk=self.pk).update(
                                audio_path=MEDIA_URL.lstrip("/")
                                + path_template
                                + file_path
                            )
                    except Exception as error:
                        log.error(
                            "%s: ERROR => %s",
                            (
                                VideoContentModel.__class__.__name__
                                + "."
                                + self.save.__name__,
                                error,
                            ),
                        )

            else:
                kwargs_audio = {
                    "title": self.title,
                    "counter": self.counter,
                    "order": self.order,
                    "content_type": self.content_type,
                    "audio_url": self.audio_url,
                    "audio_path": self.audio_path,
                    "is_active": self.is_active,
                    "upload_status": self.upload_status,
                }
                transaction_update("content_audiocontentmodel", self.id, **kwargs_audio)

            # Temporary file
            temp_path = f'{MEDIA_URL.lstrip("/")}{file_name.split("/video/")[-1]}'
            kwargs_audio = {
                "video_id": self.id,
                "temp_path": temp_path,
                "file_name": file_name,
            }
            # create the temporary file
            read_bool = True
            with open(temp_path, "wb") as f:
                while read_bool:
                    chunk = self._audio_file.read(10 * 1024 * 1024)
                    if chunk:
                        f.write(chunk)
                    else:
                        read_bool = False
            threading.Thread(target=loop_upload, kwargs=kwargs_audio).start()

    def set_audio_file(self, file):
        """Method for sending a file to the initial file's processing"""
        self._audio_file = file

    class Meta:
        verbose_name = _("Audio Content")
        verbose_name_plural = _("Audio Contents")
