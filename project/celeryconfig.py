"""
project/celeryconfig.py
"""

broker_url = "redis://83.166.245.209:6381/0"
result_backend = "redis://83.166.245.209:6381/0"

task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]
timezone = "Asia/Krasnoyarsk"
enable_utc = True

# Увеличиваем таймауты

broker_transport_options = {
    "visibility_timeout": 3600,  # 1 час
    "socket_timeout": 3600,  # Таймаут сокета (в секундах)
    "socket_connect_timeout": 30,  # Таймаут подключения
    "retry_on_timeout": True,  # Повтор при таймауте
    "max_retries": 3,  # Максимальное количество попыток
}


# THe True when need the sync
# task_always_eager = False

# quantity of workers
worker_concurrency = 1
worker_prefetch_multiplier = 1
