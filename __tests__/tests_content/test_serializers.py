from content.content_api.serializers import VideoContentSerializer


class TestContentPageSerializer:
    """Test cases for ContentPage serializer"""

    def test_serializer_missing_required_fields(self):
        """Test serializer with missing required fields"""
        data = {
            "video_path": "media/2025/07/12/video/your-file.mp4",
            "video_url": "https://fdsfsdfa.ru/dasdasdas/",
            "subtitles_url": "https://fdsfsdfa.ru/dasdasdas/",
            # Missing url, content, etc.
        }

        serializer = VideoContentSerializer(data=data)
        assert not serializer.is_valid()
        assert "video_url" in serializer.errors
        assert "subtitles_url" in serializer.errors
