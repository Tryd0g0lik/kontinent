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
from http.client import responses
from typing import List

from cfgv import ValidationError
from channels.utils import await_many_dispatch
from django.http import HttpRequest
from django.utils.decorators import method_decorator
from django.core.cache import cache
from rest_framework import status, serializers
from rest_framework.response import Response
from adrf.viewsets import ReadOnlyModelViewSet as AsyncReadOnlyModelViewSet
from content.content_api.serializers import PageDetailSerializer
from content.models import PageModel

from logs import configure_logging

log = logging.getLogger(__name__)
configure_logging(logging.INFO)


class PageDetailView(AsyncReadOnlyModelViewSet):
    queryset = PageModel.objects.all()
    serializer_class = PageDetailSerializer

    async def list(self, request: HttpRequest, *args, **kwargs) -> Response:
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
            response.data = f"%s: Error => %s" % (
                PageDetailView.__class__.__name__ + "." + self.list.__name__,
                error.args[0],
            )
            return response

    async def retrieve(self, request, *args, **kwargs) -> Response:
        """
        This method get a single content by properties of 'kwargs.pk'.
        :param HttpRequest request:
        :param args: this parameter is empty
        :param dict kwargs: '{"pk": int}' Index from db's line.
        :return:
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
