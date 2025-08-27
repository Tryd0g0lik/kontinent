from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from content.models import PageModel
from content.models_content_files import AudioContentModel, VideoContentModel


class TitleStartsWithFilter(SimpleListFilter):
    title = "Заголовок начинается с"
    parameter_name = "title_start"

    def lookups(self, request, model_admin):
        return [
            ("a", "A"),
            ("b", "B"),
            ("c", "C"),
            # Добавьте другие буквы по необходимости
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(title__istartswith=self.value())
        return queryset


class ContentInline(admin.StackedInline):
    extra = 1
    ordering = []  # 'order'


class VideoContentInline(ContentInline):
    model = VideoContentModel
    fields = ["title", "video_url", "subtitles_url", "order", "counter"]


class AudioContentInline(ContentInline):
    model = AudioContentModel
    fields = ["title", "text", "order", "counter"]


@admin.register(PageModel)
class PageAdmin(admin.ModelAdmin):
    list_display = [
        "title",
    ]
    list_filter = [
        TitleStartsWithFilter,
    ]
    search_fields = ["title"]
    inlines = [VideoContentInline, AudioContentInline]
    # ordering = ['-created_at']


@admin.register(VideoContentModel)
class VideoContentAdmin(admin.ModelAdmin):
    list_display = ["title", "page", "counter", "order"]
    list_filter = [TitleStartsWithFilter, "page"]
    search_fields = ["title"]
    ordering = ["page", "order"]


@admin.register(AudioContentModel)
class AudioContentAdmin(admin.ModelAdmin):
    list_display = ["title", "page", "counter", "order"]
    list_filter = [TitleStartsWithFilter, "page"]
    search_fields = ["title"]
    ordering = ["page", "order"]
