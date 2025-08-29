"""
content/models_content_files.py
"""

from django.db import models
from django.core import validators
from django.utils.translation import gettext_lazy as _

from content.models import ContentFileBaseModel


class VideoContentModel(ContentFileBaseModel):
    """
    Video Content Model
    """

    video_path = models.FileField(
        upload_to="%Y/%m/%d/video/",
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

    def save(self, *args, **kwargs):
        self.content_type = "video"
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("Video Content")
        verbose_name_plural = _("Video Contents")


class AudioContentModel(ContentFileBaseModel):
    """
    Audio Content Model
    """

    audio_path = models.FileField(
        upload_to="%Y/%m/%d/audio/",
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

    def save(self, *args, **kwargs):
        self.content_type = "audio"
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("Audio Content")
        verbose_name_plural = _("Audio Contents")
