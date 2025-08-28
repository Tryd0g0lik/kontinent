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
from django.http import HttpRequest, HttpResponse
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


def handler_of_task(data_list: list) -> List[dict]:
    data_pages_list: List[InitialPage] = [
        (
            views.__getitem__("data").__getitem__("contents")
            if "data" in views.keys()
            else views.__getitem__("contents")
        )
        for views in data_list
    ]
    data_numbers_list: List[dict] = [
        (
            {
                "content_type": view[0].__getitem__("content_type"),
                "id": view[0].__getitem__("id"),
            }
            if not isinstance(view, list)
            else [
                {
                    "content_type": v.__getitem__("content_type"),
                    "id": v.__getitem__("id"),
                }
                for v in view
            ]
        )
        for view in data_pages_list
    ]
    return data_numbers_list


class PageDetailView(AsyncReadOnlyModelViewSet):
    queryset = PageModel.objects.all()
    serializer_class = PageDetailSerializer

    async def list(self, request: HttpRequest, *args, **kwargs) -> Response:
        """
        Method: Get.
        ```
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
                            "video_path": "/media/2025/08/27/video/my_first_video.mp4",
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
        :param HttpRequest request:
        :param args: is empty.
        :param kwargs: is empty

        :return: HttpResponse
        """
        response = Response(status=status.HTTP_404_NOT_FOUND)
        try:
            caching_key = f"page_data_{request.get_full_path()}"
            # THE CACHE GET. Now, are trying the get the data from the cache
            cache_get = await asyncio.to_thread(cache.get, key=caching_key)
            # The CACHE GET. Here, trying the get the data from cache
            if cache_get is not None:
                response.status_code = status.HTTP_200_OK
                response.data = (json.loads(cache_get))["data"]
                # TASK FOR CACHE"S UPDATE
                threading.Thread(
                    target=self.task_increase_counter, args=(response,)
                ).start()

                def _update_cache(resp: Response) -> None:
                    for views in response.data["results"]:
                        for view in views["contents"]:
                            view["counter"] += 1
                    self.set_cache(caching_key, resp)

                threading.Thread(target=_update_cache, args=(response,)).start()
                return response

            list = super().list
            result = await asyncio.to_thread(list, request, **kwargs)
            # CELERY's TASK FOR INCREASE COUNTER
            threading.Thread(target=self.task_increase_counter, args=(result,)).start()
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
        :return: ```json
        {
            "id": 2,
            "contents": [
                {
                    "id": 2,
                    "title": "New page",
                    "counter": 4,
                    "order": 2,
                    "content_type": "video",
                    "is_active": false,
                    "video_path": "/media/2025/08/27/video/my_first_video.mp4",
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
        ```
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
            response.data = json.loads(cache_get)["data"]

            # TASK FOR CACHE"S UPDATE
            def _update_cache(resp: Response) -> None:
                for view in response.data["contents"]:
                    view["counter"] += 1
                self.set_cache(caching_key, resp)

            threading.Thread(target=_update_cache, args=(response,)).start()
            # CELERY's TASK FOR INCREASE COUNTER
            threading.Thread(
                target=self.task_increase_counter, args=(response,)
            ).start()

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
            response.data = message + f"Error => {error.args[0]}"
            response.status_code = status.HTTP_400_BAD_REQUEST
            return response

        response.data = res
        # CELERY's TASK FOR INCREASE COUNTER
        threading.Thread(target=self.task_increase_counter, args=(response,)).start()
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

    # Get lines db's indices
    @staticmethod
    async def _task_get_list_of_indices(response: Response) -> None:
        """
        Getting indices from page's contents (audio, video) and start the celery's task
        :param response:
        :return:
        """
        data: Initial = await asyncio.to_thread(lambda: response.data)
        data_numbers_list: List[dict]
        if "results" not in list(data.keys()):
            data_numbers_list = handler_of_task([data])
        else:
            data_list: List[InitialPage] = data.__getitem__("results")
            data_numbers_list = handler_of_task(data_list)
        # # RUN THE TASK - Update content's counter
        increment_content_counter.delay((data_numbers_list,))
        return

    @staticmethod
    def task_increase_counter(response: Response):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(PageDetailView._task_get_list_of_indices(response))
