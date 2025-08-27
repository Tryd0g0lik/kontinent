from django.db import models
from django.core import validators
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class PageModel(models.Model):
    """
    This is model for basic content of a page.
    'title' is the title of the page. It's unique for each page.
    'content' is the content of the page.
    """

    title = models.CharField(
        max_length=255,
        help_text=_("This is unique page's title"),
        verbose_name=_("Title"),
        unique=True,
        validators=[
            validators.RegexValidator(
                regex=r"(^[A-ZА-Я][\w -\.,]+)", message=_("Enter valid title!")
            )
        ],
    )
    text = models.TextField(
        verbose_name=_("Text"),
        help_text=_("This is page's text. Basis content."),
        validators=[],
    )

    class Meta:
        verbose_name = _("Page")
        verbose_name_plural = _("Pages")
        ordering = ["title"]

    def __str__(self):
        return "%s" % self.title


class ContentFileBaseModel(models.Model):
    """
    This is model for basic content of a page.
    """

    CONTENT_TYPES_CHOICES = [
        ("video", _("Video")),
        ("audio", _("Audio")),
    ]
    title = models.CharField(
        max_length=255,
        help_text=_("This is unique file's title"),
        verbose_name=_("Title"),
        unique=True,
        validators=[
            validators.RegexValidator(
                regex=r"(^[A-ZА-Я][\w -\.,]+)", message=_("Enter valid title!")
            )
        ],
    )
    counter = models.PositiveIntegerField(
        default=0, help_text="Counter of views", verbose_name=_("Counter of views")
    )
    order = models.PositiveIntegerField(
        default=0, help_text="Order", verbose_name=_("Order")
    )
    content_type = models.CharField(
        max_length=10,
        choices=CONTENT_TYPES_CHOICES,
        default=CONTENT_TYPES_CHOICES[0][0],
        verbose_name=_("Content type"),
        help_text=_("Content type"),
    )

    class Meta:
        abstract = True
        ordering = ["order", "counter"]

    def __str__(self):
        return "%s" % self.title


class MiddleContentPageModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    page = models.ForeignKey(
        PageModel, verbose_name=_("Page"), on_delete=models.CASCADE
    )
    content = models.ForeignKey(
        ContentFileBaseModel, verbose_name=_("Content"), on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = _("Intermediary Content")
        verbose_name_plural = _("Intermediary Content")

    def __str__(self):
        return "%s update date: %s" % (self.content, self.updated_at)
