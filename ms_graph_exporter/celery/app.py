# -*- coding: utf-8 -*-
"""Module defines Celery app.

Configure app with additional user options available for the Celery worker.
"""
# TODO:VERIFY:20190827:01
#   Is Gevent monkey-patching below necessary when using `celery worker --pool gevent` ?
#
# fmt: off
from gevent.monkey import patch_all; patch_all()  # noqa: E702
# fmt: on
from os import environ  # noqa: I100, I201

from celery import Celery
from celery import bootsteps
from celery.utils.log import get_logger

from redbeat import RedBeatSchedulerEntry

from ms_graph_exporter.celery.config import (
    CeleryConfigDev,
    CeleryConfigProd,
    CeleryConfigTest,
)


class CustomArgs(bootsteps.Step):
    """Bootstep to handle custom options and setup of the Celery worker."""

    def __init__(self, worker, **options):
        """Initialize class instance.

        Passes User Options defined by the worker to :class:`GraphApiTask`
        base class and schedules periodic data extraction from MS Graph API
        into the post-processing queue.

        Note
        ----
        By default, no config file is expected by the app. All options are taken
        either from the command-line interface (CLI) or the execution environment
        (ENV).

        Config file takes precedence over the CLI, which in turn takes precedence
        over ENV.

        """
        from ms_graph_exporter.celery.graph_api_base import GraphApiTask

        GraphApiTask.config_update(**options)

        if options["graph_app_config"]:
            GraphApiTask.config_update_from_file()

        logger = get_logger(__name__)

        map_interval = (
            GraphApiTask._config["graph_streams"]
            * GraphApiTask._config["graph_stream_frame"]
        )

        entry = RedBeatSchedulerEntry(
            "periodic_map_streams", "graph.map_streams", map_interval, app=worker.app
        )

        logger.info("adding schedule entry, %s", entry)
        entry.save()


def add_worker_arguments(parser):
    """Configure custom options for the Celery worker."""
    parser.add_argument(
        "--app_config",
        dest="graph_app_config",
        type=str,
        default=environ.get("GRAPH_APP_CONFIG", ""),
        help="""YAML-based configuration file.

        By default, no config file is expected by the app.
        All options are taken either from the command-line
        interface (CLI) or the execution environment (ENV).

        Config file directives are the same as the CLI options
        listed below. Corresponding ENV options are upper-case
        names of CLI options prefixed with 'GRAPH_'.

        Config file takes precedence over the CLI,
        which in turn takes precedence over ENV.
        """,
    )
    parser.add_argument(
        "--client_id",
        dest="graph_client_id",
        type=str,
        default=environ.get("GRAPH_CLIENT_ID", ""),
        help="ClientId of the Service Principal with access to MS Graph API.",
    )
    parser.add_argument(
        "--client_secret",
        dest="graph_client_secret",
        type=str,
        default=environ.get("GRAPH_CLIENT_SECRET", ""),
        help="ClientSecret of the Service Principal with access to MS Graph API.",
    )
    parser.add_argument(
        "--greenlets_count",
        dest="graph_greenlets_count",
        type=int,
        default=environ.get("GRAPH_GREENLETS_COUNT", 10),
        help="Maximum number of Greenlets to spawn for each data upload task.",
    )
    parser.add_argument(
        "--page_size",
        dest="graph_page_size",
        type=int,
        default=environ.get("GRAPH_PAGE_SIZE", 50),
        help="Number of records to request from the MS Graph API in a single response.",
    )
    parser.add_argument(
        "--queue_backend",
        dest="graph_queue_backend",
        type=str,
        choices=["redis", "log"],
        default=environ.get("GRAPH_QUEUE_BACKEND", "redis"),
        help="Backend type to store exported data.",
    )
    parser.add_argument(
        "--queue_type",
        dest="graph_queue_type",
        type=str,
        choices=["list", "channel"],
        default=environ.get("GRAPH_QUEUE_TYPE", "list"),
        help="Storage queue implementation type.",
    )
    parser.add_argument(
        "--queue_key",
        dest="graph_queue_key",
        type=str,
        default=environ.get("GRAPH_QUEUE_KEY", "ms_graph_exporter"),
        help="Name of the CHANNEL or LIST where extracted data is pushed.",
    )
    parser.add_argument(
        "--redis_url",
        dest="graph_redis_url",
        type=str,
        default=environ.get("GRAPH_REDIS_URL", "redis://localhost:6379?db=0"),
        help="Connection string for Redis client.",
    )
    group_redis_pool_block = parser.add_mutually_exclusive_group(required=False)
    group_redis_pool_block.add_argument(
        "--redis_pool_block",
        dest="graph_redis_pool_block",
        action="store_true",
        help="Enable threat-safe blocking in Redis connection pool.",
    )
    group_redis_pool_block.add_argument(
        "--no-redis_pool_block",
        dest="graph_redis_pool_block",
        action="store_false",
        help="Disable threat-safe blocking blocking in Redis connection pool.",
    )
    parser.set_defaults(
        graph_redis_pool_block=environ.get("GRAPH_REDIS_POOL_BLOCK", True)
    )
    group_redis_pool_gevent_queue = parser.add_mutually_exclusive_group(required=False)
    group_redis_pool_gevent_queue.add_argument(
        "--redis_pool_gevent_queue",
        dest="graph_redis_pool_gevent_queue",
        action="store_true",
        help="Enable `gevent.queue.LifoQueue` usage in Redis connection pool.",
    )
    group_redis_pool_gevent_queue.add_argument(
        "--no-redis_pool_gevent_queue",
        dest="graph_redis_pool_gevent_queue",
        action="store_false",
        help="Disable `gevent.queue.LifoQueue` usage in Redis connection pool.",
    )
    parser.set_defaults(
        graph_redis_pool_gevent_queue=environ.get("GRAPH_REDIS_POOL_GEVENT_QUEUE", True)
    )
    parser.add_argument(
        "--redis_pool_max_connections",
        dest="graph_redis_pool_max_connections",
        type=int,
        default=environ.get("GRAPH_REDIS_POOL_MAX_CONNECTIONS", 15),
        help="""Maximum number of reusable connections maintained by the connection pool
        of the Redis client.""",
    ),
    parser.add_argument(
        "--redis_pool_timeout",
        dest="graph_redis_pool_timeout",
        type=int,
        default=environ.get("GRAPH_REDIS_POOL_TIMEOUT", 1),
        help="""Time that blocking-enabled Redis client waits for connection to become
        available from the exhausted connection pool (seconds). Afterwards, raises
        Redis ConnectionError exception.""",
    ),
    parser.add_argument(
        "--streams",
        dest="graph_streams",
        type=int,
        default=environ.get("GRAPH_STREAMS", 2),
        help="Number of parallel streams to fetch time-domain data.",
    ),
    parser.add_argument(
        "--stream_frame",
        dest="graph_stream_frame",
        type=int,
        default=environ.get("GRAPH_STREAM_FRAME", 30),
        help="Time-domain size of the data request for each stream (seconds).",
    ),
    parser.add_argument(
        "--tenant",
        dest="graph_tenant",
        type=str,
        default=environ.get("GRAPH_TENANT", ""),
        help="""Azure AD tenant where the Service Principal
        with access rights to call the MS Graph API resides.
        """,
    ),
    parser.add_argument(
        "--timelag",
        dest="graph_timelag",
        type=int,
        default=environ.get("GRAPH_TIMELAG", 120),
        help="""Seconds to shift back the query time-frame for each
        of the periodic invocations of the parallelized extraction process.""",
    ),


celery_app: Celery = Celery()

conf_type: str = environ.get("GRAPH_ENV", "development")

if conf_type == "development":
    celery_app.config_from_object(CeleryConfigDev)
elif conf_type == "production":
    celery_app.config_from_object(CeleryConfigProd)
elif conf_type == "testing":
    celery_app.config_from_object(CeleryConfigTest)

celery_app.user_options["worker"].add(add_worker_arguments)
celery_app.steps["worker"].add(CustomArgs)


if __name__ == "__main__":
    celery_app.start()
