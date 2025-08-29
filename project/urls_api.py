"""
project/urls_api.py
"""

from django.urls import path, include
from content.urls_api import urlpatterns as content_api_urls

urlpatterns = [
    path("page/", include(content_api_urls)),  #  "api_content_keys")
]
