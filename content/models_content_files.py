from django.db import models
from django.core import validators
from django.utils.translation import gettext_lazy as _
from content.models import MiddleContentPageModel


class VideoContentModel(MiddleContentPageModel):
    """
    Video Content Model
    """

    video_url = models.URLField(
        verbose_name=_("Video URL"),
        help_text=_("Pathname to the video file"),
        validators=[
            validators.RegexValidator(
                regex=r"(^[a-z][a-z0-9-\/_]+\/$)", message=_("Enter valid URL!")
            )
        ],
    )
    subtitles_url = models.URLField(
        blank=True,
        null=True,
        verbose_name=_("Subtitles URL"),
        help_text=_("Pathname to the subtitles file"),
        validators=[
            validators.RegexValidator(
                regex=r"(^[a-z][a-z0-9-\/_]+\/$)", message=_("Enter valid URL!")
            )
        ],
    )

    def save(self, *args, **kwargs):
        self.content_type = "video"
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("Video Content")
        verbose_name_plural = _("Video Contents")


class AudioContentModel(MiddleContentPageModel):
    """
    Audio Content Model
    """

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
