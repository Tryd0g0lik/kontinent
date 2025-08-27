from django.urls import path, include
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r"content", basename="contents")

urlpatterns = [
    path("", include(router.urls), name="contents_api"),
]
