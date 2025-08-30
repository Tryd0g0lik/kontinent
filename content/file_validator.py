"""
content/file_validator.py
https://docs.djangoproject.com/en/4.2/ref/files/storage/#django.core.files.storage.DefaultStorage
"""

import os
import hashlib
import logging
from typing import List, Union
from django.core.files.uploadedfile import UploadedFile
from django.core.files.storage import default_storage
from project import settings
from logs import configure_logging
from content.models_content_files import (VideoContentModel, AudioContentModel)
from project.settings import DEFAULT_CHUNK_SIZE, FIELD_NAME_LIST, MEDIA_URL

log = logging.getLogger(__name__)
configure_logging(logging.INFO)


class FileDuplicateChecker:
    """
    This is the class for checking of file through library hash's MD5

    """

    def __init__(self, storage=None):
        self.storage = storage or default_storage
        self.hash_map = {}  # This is the cache how source the  path to the file

    def calculate_md5(self, file_obj, chunk_size=DEFAULT_CHUNK_SIZE) -> hashlib.md5:
        """
        Calculate the MD5 hash of file
        :param file_obj:
        :param int chunk_size: This is size a single chunk of file when separating  the whole file and after it, we be beginning  to file's read.
        :return: >>> md5_hash(b"Nobody inspects the spammish repetition").hexdigest()
        'a4337bc45a8fc544c03f52dc550cd6e1e87021bc896588bd79e901e2'
        """

        md5_hash = hashlib.md5()

        if isinstance(file_obj, UploadedFile):
            # Separating of file by chunk and after read the file and yield chunks of ``DEFAULT_CHUNK_SIZE`` bytes

            for chunk in file_obj.chunks(chunk_size):
                # FOr loaded files from the Django
                md5_hash.update(chunk)
            # Return the size to the beginning
            file_obj.seek(0)
        path_list = FIELD_NAME_LIST[:3].copy()
        for path in path_list + ["video", "audio"]:
            if hasattr(file_obj, path):
                # For FileField objects
                p = MEDIA_URL.lstrip("/") + file_obj.video_path.name if not "media/" in file_obj.video_path.name \
                    else file_obj.video_path.name
                with open(p, "rb") as file:
                    for chunk in iter(lambda: file.read(chunk_size), b""):
                        md5_hash.update(chunk)
                path_list.clear()
            elif isinstance(file_obj, str) and os.path.exists(file_obj if MEDIA_URL.lstrip("/") in file_obj\
                    else MEDIA_URL.lstrip("/") + file_obj):
                # For file paths
                with open((file_obj if MEDIA_URL.lstrip("/") in file_obj\
                    else MEDIA_URL.lstrip("/") + file_obj), "rb") as file:
                    # for chunk in iter(lambda: file.read(size=chunk_size), b""):
                    md5_hash.update(file.read())
                path_list.clear()
        return md5_hash.hexdigest()

    def check_duplicate(
        self,
        file_obj,
        model_class: Union[VideoContentModel, AudioContentModel] = None,
        field_name_list: List[str] = None,
    ) -> str | None:
        """
        This's checker - file exists into the MD5's hash or not.
        If is True it's mean returning the path to the MD5's hash.
        :param file_obj:
        :param Union[VideoContentModel, AudioContentModel] model_class:
        :param List[str] field_name_list:  Value by default has 'FIELD_NAME_LIST' or '["audio_path", "audio_url", "video_url", "video_path"]'
        :return:
        """
        field_name_list = (
            field_name_list if field_name_list is not None else FIELD_NAME_LIST
        )
        try:
            if isinstance(file_obj, str) and file_obj.startswith(
                ("http://", "https://")
            ):
                return None
            file_md5 = self.calculate_md5(file_obj)
            if not file_md5:
                return None
            # Check the cache.
            if file_md5 in self.hash_map.keys():
                existing_path = self.hash_map[file_md5]
                return existing_path
            # Check into the db.
            for field_name in field_name_list:
                if hasattr(model_class, field_name):
                    existing_path = self._check_in_database(
                        model_class, file_md5, [field_name]
                    )
                    if existing_path:
                        file_path = getattr(existing_path, field_name)
                        self.hash_map[file_md5] = file_path
                        return file_path
            # Check into the file's source
            existing_path = self._check_in_storage(file_md5)
            if existing_path:
                self.hash_map[file_md5] = existing_path
                return existing_path
            return None
        except Exception as error:
            log.error(
                "%s: Error => %s"
                % (
                    FileDuplicateChecker.__class__.__name__
                    + "."
                    + self.check_duplicate.__name__,
                    error.args[0],
                )
            )
            return None

    def _check_in_database(
        self,
        model_class: Union[VideoContentModel, AudioContentModel],
        file_md5,
        field_name_list: List[str] = None,
    ) -> Union[VideoContentModel, AudioContentModel, None]:
        """
        Look up the files which could has the same names
        :param Union[VideoContentModel, AudioContentModel] model_class:
        :param List[str] field_name_list:  Value by default has 'FIELD_NAME_LIST' or '["audio_path", "audio_url", "video_url", "video_path"]'
        :param str file_md5: this hash's string.
        :return:  Returning the obj from db or None
        """
        field_name_list = (
            field_name_list if field_name_list is not None else FIELD_NAME_LIST
        )
        try:
            obj_iter = (obj for obj in model_class.objects.all())
            for obj in obj_iter:
                for name in field_name_list:
                    file_field = getattr(obj, name)
                    return (
                        obj
                        if file_field
                        and self.calculate_md5(file_field.path) == file_md5
                        else None
                    )
        except Exception as error:
            log.error(
                "%s: Error => %s"
                % (
                    FileDuplicateChecker.__class__.__name__
                    + "."
                    + self.check_duplicate.__name__,
                    error.args[0],
                )
            )
            return None

    def _check_in_storage(self, file_md5) -> Union[str, None]:
        """
        :param str file_md5: this hash's string.
        :return: Returning the string's path or None
        """
        # Check all the files to the MEDIA's directory
        media_root = getattr(settings, "MEDIA_ROOT", "")
        if not media_root:
            return None

        for root, dirs, files in os.walk(media_root):
            file_path_iter = (os.path.join(root, file_path) for file_path in files)
            for file_path in file_path_iter:
                try:
                    file_md5_current = self.calculate_md5(file_path)
                    if file_md5_current == file_md5:
                        # Return pathname from django (it's old path)
                        relative_path = os.path.relpath(file_path, media_root)
                        return relative_path
                except (IOError, OSError, Exception) as error:
                    log.error(
                        "%s: Error => %s"
                        % (
                            FileDuplicateChecker.__class__.__name__
                            + "."
                            + self.check_duplicate.__name__,
                            error.args[0],
                        )
                    )
                    return None

    def add_file_hash(self, file_path: str, file_md5: str) -> None:
        """
        This is adding the itself file and him a cache to the hash
        :param str file_md5: name from hash.
        :param str file_path: This path to the file's source
        :return:
        """
        self.hash_map[file_md5] = file_path

    def clear_cache(self) -> None:
        self.hash_map.clear()
        # The end.
