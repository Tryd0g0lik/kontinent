"""
content/transactions.py
"""

import logging
from typing import Union

from django.db import transaction, connections
from logs import configure_logging

log = logging.getLogger(__name__)
configure_logging(logging.INFO)

ALLOWED_TABLES_CONTENT = ["content_audiocontentmodel", "content_videocontentmodel"]


def transaction_update(table_db: str, index: int, **kwargs) -> None:
    """
    This is function for updating the line in db.
    :param str table_db: Name table from db
    :param int index: Number of string/line which we want to update
    :param dict kwargs: '{< name_of_one_column>: < new_value >, ...}'
    :return: None
    """
    message = "%s: " % transaction_update.__name__
    with transaction.atomic():
        # Check
        if table_db not in ALLOWED_TABLES_CONTENT:
            log.error(message + f"ERROR => 'ALLOWED_TABLES' not valid - {table_db}")
            return
        for col in kwargs.keys():
            if not col.replace("_", "").isalnum():
                log.error(message + f"ERROR => is not correct the column name - {col}")
        # SQL
        set_clause = ", ".join([f"{col} = %s" for col in kwargs.keys()])
        query = f"""UPDATE {table_db} SET {set_clause} WHERE id = %s"""

        with connections["default"].cursor() as cursor:
            try:
                cursor.execute(query, list(kwargs.values()) + [index])
            except Exception as error:
                log.error(message + f"ERROR => {error.args[0]}")
            finally:
                cursor.close()


def transaction_get(table_db: str, index: int) -> Union[dict, None]:
    """
    This is function for updating the line in db.
    :param str table_db: Name table from db
    :param int index: Number of string/line which we want to update
    :param dict kwargs: '{< name_of_one_column>: < new_value >, ...}'
    :return: dict or None
    """
    message = "%s: " % transaction_update.__name__
    with transaction.atomic():
        # Check
        if table_db not in ALLOWED_TABLES_CONTENT:
            log.error(message + f"ERROR => 'ALLOWED_TABLES' not valid - {table_db}")
            return
        # SQL
        query = f"""SELECT * FROM {table_db} WHERE id = %s"""

        with connections["default"].cursor() as cursor:
            try:
                cursor.execute(query, [index])
                keys_list = [k_list[0] for k_list in cursor.description]
                v_dict = dict(zip(keys_list, list(cursor.fetchone())))
                return v_dict
            except Exception as error:
                log.error(message + f"ERROR => {error.args[0]}")
            finally:
                cursor.close()
