"""
content/content_api/views_api.py
Methods is use polymorphism for get text-data
to the log file when we get error in your logic.
Logic of code itself almost is copy from basis django's code.
Logic itself don't have anything the permissions for users. This code can use for anyone  user's role.
"""

import asyncio
import json
import logging
import threading
from typing import List, TypedDict, NotRequired

from cfgv import ValidationError
from django.http import HttpRequest
from django.core.cache import cache
from rest_framework import status, serializers
from rest_framework.response import Response
from adrf.viewsets import ReadOnlyModelViewSet as AsyncReadOnlyModelViewSet
from content.content_api.serializers import PageDetailSerializer
from content.models import PageModel
from content.tasks import increment_content_counter
from logs import configure_logging

log = logging.getLogger(__name__)
configure_logging(logging.INFO)


class InitialContent(TypedDict):
    id: int | str
    title: str
    counter: int | str
    order: int | str
    content_type: str
    is_active: bool
    video_path: NotRequired[str]
    video_url: NotRequired[str]
    subtitles_url: NotRequired[str]
    audio_path: NotRequired[str]
    audio_url: NotRequired[str]


class InitialPage(TypedDict):
    id: int | str
    contents: List[InitialContent]
    created_at: str
    updated_at: str
    url: str
    title: str
    text: str


class Initial(TypedDict):
    count: int
    next: NotRequired[int]
    previous: any
    results: List[InitialPage]


class PageDetailView(AsyncReadOnlyModelViewSet):
    queryset = PageModel.objects.all()
    serializer_class = PageDetailSerializer

    async def list(self, request: HttpRequest, *args, **kwargs) -> Response:
        """
        Method: Get.
        :param HttpRequest request:
        :param args: is empty.
        :param kwargs: is empty
        :return: ```json
                {
            "count": 1,
            "next": null,
            "previous": null,
            "results": [
                {
                    "id": 2,
                    "contents": [
                        {
                            "id": 2,
                            "title": "New page",
                            "counter": 0,
                            "order": 2,
                            "content_type": "video",
                            "is_active": false,
                            "video_path": "/media/2025/08/27/video/%D0%AD%D1%82%D0%B8_%D1%81%D1%82%D1%80%D0%B0%D1%88%D0%BD%D1%8B%D0%B5_%D0%B1%D1%83%D0%BA%D0%B2%D1%8B_MV.mp4",
                            "video_url": null,
                            "subtitles_url": null
                        }
                    ],
                    "created_at": "2025-08-27T16:39:30.072225+07:00",
                    "updated_at": "2025-08-27T16:39:30.073226+07:00",
                    "url": "http://dasdas.ru/freelance_django/",
                    "title": "New Video Content",
                    "text": "This is page's text. Basis content."
                }
            ]
        }
        ```
        """
        response = Response(status=status.HTTP_404_NOT_FOUND)
        try:
            caching_key = f"page_data_{request.get_full_path()}"
            # THE CACHE GET. Now, are trying get the data from the cache
            cache_get = await asyncio.to_thread(cache.get, key=caching_key)
            # The CACHE GET. Here, trying get the data from cache
            if cache_get is not None:
                response.status_code = status.HTTP_200_OK
                response.data = (json.loads(cache_get))["data"]
                return response

            list = super().list
            result = await asyncio.to_thread(list, request, **kwargs)

            # Get lines db's indices
            async def task_get_list_of_indices(response: Response) -> None:
                """
                Getting indices from page's contents (audio, video) and run the counter
                :param response:
                :return:
                """
                data: Initial = await asyncio.to_thread(lambda: response.data)
                if not data.__getitem__("results"):
                    return []
                data_list: List[InitialPage] = data.__getitem__("results")

                data_pages_list: List[InitialPage] = [
                    views.__getitem__("contents") for views in data_list
                ][0]
                data_numbers_list: List[dict] = [
                    {
                        "content_type": view.__getitem__("content_type"),
                        "id": view.__getitem__("id"),
                    }
                    for view in data_pages_list
                ]
                # # RUN THE TASK - Update content's counter
                increment_content_counter.delay((data_numbers_list,))
                return

            def task_increase_counter(response: Response):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(task_get_list_of_indices(response))

            threading.Thread(target=task_increase_counter, args=(result,)).start()
            # The CACHE SET. Here trying set the data to the cache
            threading.Thread(target=self.set_cache, args=(caching_key, result)).start()
            return result
        except Exception as error:
            log.error(
                "%s: Error => %s"
                % (
                    PageDetailView.__class__.__name__ + "." + self.list.__name__,
                    error.args[0],
                )
            )
            response.data = "%s: Error => %s" % (
                PageDetailView.__class__.__name__ + "." + self.list.__name__,
                error.args[0],
            )
            return response

    async def retrieve(self, request, *args, **kwargs) -> Response:
        """
        Method: Get.
        This method get a single content by properties of 'kwargs.pk'.
        :param HttpRequest request:
        :param args: this parameter is empty
        :param dict kwargs: '{"pk": int}' Index from db's line.
        :return: HttpResponse
        """
        message = (
            "%s:" % PageDetailView.__class__.__name__ + "." + self.retrieve.__name__
        )
        response = Response(status=status.HTTP_404_NOT_FOUND)
        index = kwargs.get("pk")
        file_list: List[PageModel] = []
        caching_key = f"page_data_{index}_{request.get_full_path()}"
        # THE CACHE GET. Now, are trying get the data from the cache
        cache_get = await asyncio.to_thread(cache.get, key=caching_key)
        if cache_get is not None:
            response.status_code = status.HTTP_200_OK
            response.data = json.loads(cache_get)
            return response
        try:
            file_list.extend([view async for view in self.queryset.filter(pk=index)])
        except Exception as error:
            log.error(message + f"Error => {error.args[0]}")
            response.data = message + f"Error => {error.args[0]}"
            return response

        if len(file_list) == 0:
            log.error(message + f"Error => Page view with pk {index} not found")
            response.data = message + f"Error => Page view with pk {index} not found"
            return response
        serializer = None
        try:
            serializer = self.serializer_class(file_list[0])
            res = await asyncio.to_thread(lambda: serializer.data)
        except ValidationError as error:
            log.error(message + f"Error => {error.args[0]}")
            response.data = {"data": message + f"Error => {error.args[0]}"}
            response.status_code = status.HTTP_400_BAD_REQUEST
            return response

        response.data = res
        response.status_code = status.HTTP_200_OK
        # THE CACHE SET. Now, are trying set the data to the cache
        threading.Thread(target=self.set_cache, args=(caching_key, response)).start()
        return response

    @staticmethod
    async def serializer_validate(serializer):
        message = (
            "%s: " % PageDetailView.__class__.__name__
            + "."
            + PageDetailView.serializer_validate.__name__
        )
        is_valid = await asyncio.create_task(asyncio.to_thread(serializer.is_valid))
        if not is_valid:
            error_test = serializer.errors
            log.error(message + "Error => %s", error_test)
            raise serializers.ValidationError(error_test)

    @staticmethod
    def set_cache(caching_key: str, response: Response) -> None:
        """
        This is sync function.
        Data is cache to the JSON's format.
        :param str caching_key: Template is '<page_data_<pk_from_url>_< pathname_from_apiurl >>'
        Exemple of 'caching_key' is the: 'page_data_2_/api/page/content/2/'.
        :param response:
        :return:
        """

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            asyncio.to_thread(
                cache.set,
                timeout=(60 * 60 * 24),
                key=caching_key,
                value=json.dumps({"data": response.data}),
            )
        )
