from django.urls import path, include
from rest_framework import routers
from content.content_api.views_api import PageDetailView

router = routers.DefaultRouter()
router.register(r"content", PageDetailView, basename="contents")

urlpatterns = [
    # path("", include(router.urls)), # "api_main_content_keys"
    path("", include(router.urls), name="api_main_content_keys"),
    # path("content/0/get/", PageDetailView.as_view({"get": "get"})),
]
