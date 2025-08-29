"""
content/content_api/additionally.py
"""

import logging
from typing import List, TypedDict, NotRequired
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
