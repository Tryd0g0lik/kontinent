broker_url = "redis://83.166.245.209:6380/0"
result_backend = "redis://83.166.245.209:6380/0"

task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]
timezone = "Asia/Krasnoyarsk"
enable_utc = True

# celery speed for handle of tasks
# task_annotations = {
#     'one_tasks.celery_task_money': {'rate_limit': '10/m'}
# }

# THe True when need the sync
# task_always_eager = False

# quantity of workers
worker_concurrency = 1
worker_prefetch_multiplier = 1
