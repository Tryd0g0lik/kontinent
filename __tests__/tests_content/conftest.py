import os
import django
from model_bakery import baker

# Configure Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
django.setup()

import pytest

from rest_framework.test import APIClient
from content.models import PageModel


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
@pytest.mark.django_db
def content_page():
    return baker.make(PageModel, _quantity=1)[0]


@pytest.fixture
@pytest.mark.django_db
def multiple_content_pages():
    pages = baker.make(PageModel, _quantity=5)
    return pages
