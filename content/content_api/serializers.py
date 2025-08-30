"""
content/content_api/serializers.py
"""

from typing import Union
from adrf import serializers

from content.file_validator import FileDuplicateChecker
from content.models import PageModel
from content.models_content_files import VideoContentModel, AudioContentModel
from rest_framework.serializers import (
    CharField,
    HyperlinkedIdentityField,
    SerializerMethodField,
)


fduplicate = FileDuplicateChecker()


class ContenBasetSerializer(serializers.ModelSerializer):
    content_type = CharField(read_only=True)

    class Meta:
        fields = ["id", "title", "counter", "order", "content_type", "is_active"]


class VideoContentSerializer(ContenBasetSerializer):
    class Meta:
        model = VideoContentModel
        fields = ContenBasetSerializer.Meta.fields + [
            "video_path",
            "video_url",
            "subtitles_url",
        ]


class AudioContentSerializer(ContenBasetSerializer):
    class Meta:
        model = AudioContentModel
        fields = ContenBasetSerializer.Meta.fields + ["audio_url", "audio_path"]


class ContentPolymorphicSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        if isinstance(instance, VideoContentModel):
            return VideoContentSerializer(
                instance, context=self.context
            ).to_representation(instance)
        elif isinstance(instance, AudioContentModel):
            return AudioContentSerializer(
                instance, context=self.context
            ).to_representation(instance)
        return None


class PageListSerializer(serializers.ModelSerializer):
    url = HyperlinkedIdentityField(view_name="page-detail", lookup_field="pk")

    class Meta:
        model = PageModel
        fields = ["title", "url"] + AudioContentSerializer.Meta.fields


class PageDetailSerializer(serializers.ModelSerializer):
    contents = SerializerMethodField()

    class Meta:
        model = PageModel
        fields = "__all__"

    def get_contents(self, obj: Union[VideoContentModel, AudioContentModel]):
        # Get all related objects of contents
        video_contents = VideoContentModel.objects.filter(page=obj)
        audio_contents = AudioContentModel.objects.filter(page=obj)

        all_contents = list(video_contents) + list(audio_contents)
        all_contents.sort(key=lambda x: x.order)

        return ContentPolymorphicSerializer(
            all_contents,
            many=True,
        ).data


type TypePageDetailSerializer = type(PageDetailSerializer)
