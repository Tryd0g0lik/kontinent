"""
content/models_content_files.py
"""

import os
import uuid
import logging
from datetime import datetime

from celery.bin.result import result
from django.db import models, connections, transaction
from django.core import validators
from django.utils.translation import gettext_lazy as _


from content.models import ContentFileBaseModel
from logs import configure_logging

from project.settings import (
    MEDIA_PATH_TEMPLATE_AUDIO,
    MEDIA_PATH_TEMPLATE_VIDEO,
    MEDIA_URL,
)

log = logging.getLogger(__name__)
configure_logging(logging.INFO)


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

    def save(self, *args, **kwargs):
        from content.tasks import task_process_video_upload

        self.content_type = "video"

        # Если есть файл для загрузки и он еще не обработан
        if hasattr(self, "_video_file") and self.upload_status != "completed":
            self.upload_status = "processing"

            # Запускаем фоновую задачу
            file_data = self._video_file.read()
            file_name = f"{uuid.uuid4()}_{self._video_file.name}"
            super().save(*args, **kwargs)
            task_process_video_upload.delay(self.id, file_data, file_name)
        if hasattr(self, "video_path") and self.upload_status != "completed":
            self.upload_status = "processing"
            self.set_video_file(self.video_path)

            # Запускаем фоновую задачу
            file_data = self._video_file.read()
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
                            self.generate_filepath(path_template, self.video_path.name)
                            self.__class__.objects.filter(pk=self.pk).update(
                                video_path="media/" + path_template + file_path
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
                with transaction.atomic():
                    with connections["default"].cursor() as cursor:
                        try:
                            cursor.execute(
                                """
                                UPDATE content_videocontentmodel VALUES(
                                %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                ) WHERE id = %s;
                            """
                                % (
                                    self.title,
                                    self.counter,
                                    self.order,
                                    self.content_type,
                                    self.video_url,
                                    self.subtitles_url,
                                    self.video_path,
                                    self.is_active,
                                    self.upload_status,
                                    self.id,
                                )
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
                        finally:
                            cursor.close()
            # task_process_video_upload.delay(self.id, file_data, file_name)
            task_process_video_upload(self.id, file_data, file_name)

    def generate_filepath(self, instance, filename):
        from pathlib import Path
        from project.settings import MEDIA_ROOT
        from content.tasks import task_cleaning_media_root

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
        task_cleaning_media_root.apply_async(
            args=[], kwargs={"path": "%s" % "media" + "\\" + filename }, countdown=60
        )

    def set_video_file(self, file):
        """Метод для установки файла для фоновой обработки"""

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

    def save(self, *args, **kwargs):
        from content.tasks import task_process_audio_upload

        self.content_type = "audio"

        # Если есть файл для загрузки и он еще не обработан
        if (
            hasattr(self, "_audio_file")
            and self._audio_file
            and self.upload_status != "completed"
        ):
            self.upload_status = "processing"
            super().save(*args, **kwargs)

            # Запускаем фоновую задачу
            file_data = self._audio_file.read()
            file_name = f"{uuid.uuid4()}_{self._audio_file.name}"

            task_process_audio_upload.delay(self.id, file_data, file_name)

        else:
            super().save(*args, **kwargs)

    def set_audio_file(self, file):
        """Метод для установки файла для фоновой обработки"""
        self._audio_file = file

    class Meta:
        verbose_name = _("Audio Content")
        verbose_name_plural = _("Audio Contents")
