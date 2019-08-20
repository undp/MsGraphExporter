# -*- coding: utf-8 -*-
"""Module defines Celery configuration objects."""
from os import environ


class CeleryConfigBase:
    """Baseline Celery app configuration."""

    beat_max_loop_interval = 300
    beat_scheduler = "redbeat.RedBeatScheduler"

    redbeat_key_prefix = "ms_graph_exporter"
    redbeat_lock_timeout = beat_max_loop_interval * 5

    # See more details at https://redbeat.readthedocs.io/en/latest/config.html
    # beat_max_loop_interval = 5
    # redbeat_redis_url = broker_url
    # redbeat_key_prefix = 'redbeat'
    # redbeat_schedule_key = redbeat_key_prefix + ':schedule'
    # redbeat_statics_key = redbeat_key_prefix + ':statics'
    # redbeat_lock_key = redbeat_key_prefix + ':lock'
    # redbeat_lock_timeout = beat_max_loop_interval * 5

    include = ("ms_graph_exporter.celery.tasks",)

    task_acks_late = True

    task_ignore_result = True

    task_routes = {
        "graph.store_records": {"queue": "graph.store"},
        "graph.fetch_stream": {"queue": "graph.fetch"},
        "graph.map_streams": {"queue": "graph.map"},
    }

    timezone = "UTC"

    # TODO:FEATURE:20190827:01
    #   Make `worker_prefetch_multiplier` a configuration option.
    #
    worker_prefetch_multiplier = 1


class CeleryConfigDev(CeleryConfigBase):
    """Celery app configuration (DEV)."""

    broker_url = environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")


class CeleryConfigProd(CeleryConfigBase):
    """Celery app configuration (PROD)."""

    broker_url = environ.get("CELERY_BROKER_URL", "redis://redis:6379/0")

    beat_max_loop_interval = 5

    redbeat_lock_timeout = beat_max_loop_interval * 3


class CeleryConfigTest(CeleryConfigBase):
    """Celery app configuration (TEST)."""

    broker_url = environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")

    task_always_eager = True
