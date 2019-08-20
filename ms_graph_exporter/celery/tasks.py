# -*- coding: utf-8 -*-
"""Module defines parallel data retrieval tasks.

Tasks use :class:`~ms_graph_exporter.celery.graph_api_base.GraphApiTask`
as a base for interaction with MS Graph API and Redis.
"""
from datetime import datetime
from typing import Any, Dict, List, Tuple

from dateutil import parser

from redis import RedisError

from requests.exceptions import ConnectionError, RequestException

from ms_graph_exporter.celery.app import celery_app
from ms_graph_exporter.celery.graph_api_base import GraphApiTask


@celery_app.task(
    base=GraphApiTask,
    name="graph.map_streams",
    bind=True,
    retry_backoff=True,
    retry_backoff_max=32,
)
def map_streams(self) -> None:
    """Split extraction into streams.

    When invoked by the scheduler, splits past time-frame between previous and current
    invocation into smaller time slices (streams) and initiates parallel data requests
    for each slice.

    Note
    ----
    The task should be executed every ``streams * stream_frame`` seconds in order
    to fully cover the elapsed time-frame between executions.

    """
    t_now: datetime = datetime.utcnow().replace(microsecond=0)

    time_slices: List[Tuple[datetime, datetime]] = self.task_get_time_slices(t_now)

    for (slice_start, slice_end) in time_slices:
        fetch_stream.delay(slice_start.isoformat(), slice_end.isoformat())


@celery_app.task(
    base=GraphApiTask,
    name="graph.fetch_stream",
    bind=True,
    autoretry_for=(RequestException, ConnectionError),
    retry_backoff=True,
    retry_backoff_max=32,
)
def fetch_stream(self, slice_start: str, slice_end: str) -> None:
    """Get a slice of records.

    Request time-domain data slice ``[slice_start - slice_end]`` and paginate through
    the response passing each page of records to a dedicated queuing task.

    Parameters
    ----------
    slice_start
        Beginning of the data slice (ISO 8601 formated timestamp).

    slice_end
        End of the data slice (ISO 8601 formated timestamp).

    """
    t_start: datetime = parser.parse(slice_start)
    t_end: datetime = parser.parse(slice_end)

    self._logger.info(
        "Fetch stream [%s - %s]",
        "{}.0000000Z".format(t_start.isoformat()),
        "{}.9999999Z".format(t_end.isoformat()),
    )

    data_slice = self.task_fetch_slice(slice_start=t_start, slice_end=t_end)

    for page in data_slice:
        store_records.delay(page)


@celery_app.task(
    base=GraphApiTask,
    name="graph.store_records",
    bind=True,
    autoretry_for=(RedisError,),
    retry_backoff=True,
    retry_backoff_max=64,
    max_retries=5,
)
def store_records(self, records: List[Dict[str, Any]]) -> None:
    """Store records.

    Use Redis client to push ``records`` into a list or publish
    under a channel mentioned in the app config. Just log data,
    if the queue client is not instantiated.

    Parameters
    ----------
    records
        List of records to queue.

    """
    if self._config["graph_queue_backend"].lower() == "redis":
        redis_client = self.redis_client

        self._logger.info(
            "Redis[%s]: Attempting to push %s records", id(redis_client), len(records)
        )
        result = self.task_redis_push_multi_imap(records)

        if result:
            self._logger.info(
                "Redis[%s]: Pushed %s records", id(redis_client), len(records)
            )
        else:
            self._logger.warning("Redis[%s]: Failure pushing records", id(redis_client))
            raise RedisError

    elif self._config["graph_queue_backend"].lower() == "log":
        self._logger.info("Logging %s records", len(records))

        self.task_records_to_log(records)
