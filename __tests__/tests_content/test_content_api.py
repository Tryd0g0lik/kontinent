import json
import logging
import pytest

from django.urls import reverse
from rest_framework import status
from content.models import PageModel  # Adjust based on your actual model
from model_bakery import baker
from logs import configure_logging

log = logging.getLogger(__name__)
configure_logging(logging.INFO)


class TestContentPageAPI:
    """Test cases for Content Page API endpoints"""

    @pytest.mark.django_db
    def test_get_content_page_list_filter_published(
        self, api_client, multiple_content_pages
    ):
        """Test that only published pages are returned for unauthenticated users"""
        url = reverse("api_keys:contents-list")

        response = api_client.get(url)

        # Verify all returned pages are published
        for page_data in response.data["results"]:
            assert page_data["is_active"] is True

    @pytest.mark.django_db
    def test_get_content_page_list_pagination(self, api_client, multiple_content_pages):
        """Test that list endpoint returns paginated results"""
        url = reverse("api_keys:contents-list")

        response = api_client.get(url)

        assert "count" in response.data
        assert "next" in response.data
        assert "previous" in response.data
        assert "results" in response.data

    @pytest.mark.django_db
    def test_get_content_page_list_ordering(self, api_client, multiple_content_pages):
        """Test that pages are ordered correctly"""
        url = reverse("api_keys:contents-list")

        response = api_client.get(url)

        # Check if pages are ordered by 'order' field
        orders = [page["order"] for page in response.data["results"]]
        assert orders == sorted(orders)

    @pytest.mark.django_db
    def test_get_nonexistent_content_page(self, api_client):
        """Test retrieving non-existent content page"""
        url = reverse("api_keys:contents-detail", kwargs={"pk": 9999})

        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestContentPageAPIPerformance:
    """Performance tests for Content Page API"""

    def test_content_page_list_performance(self, api_client, db):
        """Test that list endpoint performs well with many pages"""
        # Create multiple pages for performance testing
        for i in range(100):
            kwargs = {
                "title": f"Performance Page {i}",
            }
            baker.make(PageModel, **kwargs, _quantity=1)

        url = reverse("api_keys:contents-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) <= 10  # Assuming default pagination size
