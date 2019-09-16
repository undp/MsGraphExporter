# -*- coding: utf-8 -*-
"""Module implements base class :class:`GraphApiTask` for data extraction Celery tasks.

:class:`GraphApiTask` defines Redis and MS Graph API clients as attributes to be shared
by all tasks within a Celery worker.
"""
from datetime import datetime, timedelta
from functools import partial
from json import dumps as json_dumps
from logging import Logger
from typing import Any, Callable, Dict, List, Optional, Tuple

from celery import Task
from celery.utils.log import get_task_logger

import gevent
from gevent.pool import Group

from redis import BlockingConnectionPool, ConnectionPool, RedisError
from redis.client import Redis

from yaml import YAMLError, safe_load

from ms_graph_exporter.ms_graph.api import MsGraph
from ms_graph_exporter.ms_graph.response import MsGraphResponse


class GraphApiTask(Task):
    """Base class for MS Graph API data extraction Celery tasks.

    Allows to share instances of Redis connection pool
    :class:`BlockingConnectionPool <redis:redis.BlockingConnectionPool>`
    and :class:`~ms_graph_exporter.ms_graph.api.MsGraph` between all tasks
    executed within a single Celery worker.

    Attributes
    ----------
    _config : :obj:`~typing.Dict` [:obj:`str`, :obj:`~typing.Any`]
        Dictionary holding configuration parameters that are
        initialized by the worker on startup.

    _logger : :obj:`~logging.Logger`
        Channel to be used for log output specific to the worker.

    _ms_graph : :obj:`~ms_graph_exporter.ms_graph.api.MsGraph`
        Ms Graph API client instance to be used for queries.

    _redis_pool : :obj:`Redis <redis:redis.BlockingConnectionPool>`
        Connection pool to be used by Redis clients for response data queuing.

    """

    _config: Dict[str, Any] = {
        "graph_app_config": "instance/app_config.yaml",
        "graph_client_id": "",
        "graph_client_secret": "",
        "graph_greenlets_count": 10,
        "graph_page_size": 50,
        "graph_queue_backend": "redis",
        "graph_queue_type": "list",
        "graph_queue_key": "ms_graph_exporter",
        "graph_redis_url": "redis://localhost:6379?db=0",
        "graph_redis_pool_block": True,
        "graph_redis_pool_gevent_queue": True,
        "graph_redis_pool_max_connections": 15,
        "graph_redis_pool_timeout": 1,
        "graph_streams": 1,
        "graph_stream_frame": 60,
        "graph_tenant": "",
        "graph_timelag": 120,
    }

    _logger: Logger = get_task_logger(__name__)

    _ms_graph: Optional[MsGraph] = None

    _redis_conn_pool: Optional[ConnectionPool] = None

    _redis_client: Optional[Redis] = None

    _redis_methods_map: Dict[str, str] = {"list": "RPUSH", "channel": "PUBLISH"}
    """Map between Redis queue types and data pushing operation."""

    @classmethod
    def config_update(cls, **options) -> None:
        """Update internal configuration.

        Accept arbitrary set of keyword arguments and update ``_config`` dict
        with all values matching keys defined there initially.

        Parameters
        ----------
        **options
            Set of arbitrary keyword arguments used to update ``_config``.

        """
        cls._logger.debug("[%s]: Update config from kwargs.", cls.__name__)

        config_update: Dict = {k: options[k] for k in options.keys() if "graph_" in k}

        cls._config.update(config_update)

        cls._logger.debug("[%s]: Final config: %s", cls.__name__, cls._config)

    @classmethod
    def config_update_from_file(cls, config_file: str = None) -> None:
        """Update internal configuration from file.

        Read YAML ``config_file`` and update ``_config`` dict with all values matching
        keys defined there initially.

        Parameters
        ----------
        config_file
            Path to YAML config file. If not defined, tries to load file mentioned
            in ``_config["graph_app_config"]``

        """
        if config_file is None:
            config_file = cls._config["graph_app_config"]

        if config_file != "":
            cls._logger.debug(
                "[%s]: Update config from file: %s", cls.__name__, config_file
            )

            cls._config["graph_app_config"] = config_file

            config_yaml: Dict = {}
            with open(config_file, "r") as f:
                try:
                    config_yaml = safe_load(f)
                except YAMLError:
                    cls._logger.exception(
                        "Exception loading config file '%s'", config_file
                    )

            if config_yaml:
                config_update = {
                    "graph_{}".format(k): config_yaml.get(k, None)
                    for k in config_yaml.keys()
                }

                cls._config.update(config_update)

                cls._logger.debug("[%s]: Final config: %s", cls.__name__, cls._config)

    @property
    def graph(self) -> MsGraph:
        """Provide a shared instance of MS Graph API client."""
        if self._ms_graph is None:
            self._ms_graph = MsGraph(
                client_id=self._config["graph_client_id"],
                client_secret=self._config["graph_client_secret"],
                tenant=self._config["graph_tenant"],
            )

        return self._ms_graph

    def _records_to_redis_naive(self, records: List[Any]) -> bool:
        """Push records to Redis.

        Push ``records`` into a Redis list or publish in a channel. Does not
        apply any optimizations. Yields control to Gevent Hub at each iteration.

        Parameters
        ----------
        records
            List of records to store.

        Returns
        -------
        bool
            Flag indicating success or failure of the operation.

        """
        redis_client: Redis = self.redis_client

        queue_type: str = self._config["graph_queue_type"]
        queue_key: str = self._config["graph_queue_key"]

        try:
            redis_action = getattr(
                redis_client, self._redis_methods_map[queue_type].lower()
            )

            for r in records:
                gevent.sleep()
                redis_action(queue_key, json_dumps(r))

        except RedisError as e:
            self._logger.exception("Redis Exception: %s", str(e))  # noqa: G200
            result = False

        else:
            result = True

        return result

    def _records_to_redis_pipe(self, records: List[Any]) -> bool:
        """Push records to Redis with pipelining.

        Push ``records`` into a list or publish in a channel. Utilize pipelining to
        minimize connection overhead. Yields control to Gevent Hub at each iteration.

        Parameters
        ----------
        records
            List of records to store.

        Returns
        -------
        bool
            Flag indicating success or failure of the operation.

        """
        redis_client: Redis = self.redis_client

        queue_type: str = self._config["graph_queue_type"]
        queue_key: str = self._config["graph_queue_key"]

        try:
            with redis_client.pipeline() as pipe:

                pipe.multi()

                redis_action = getattr(
                    pipe, self._redis_methods_map[queue_type].lower()
                )

                for r in records:
                    gevent.sleep()
                    redis_action(queue_key, json_dumps(r))

                pipe.execute()

        except RedisError as e:
            self._logger.exception("Redis Exception: %s", str(e))  # noqa: G200
            result = False

        else:
            result = True

        return result

    @property
    def redis_client(self) -> Redis:
        """Provide an instance of Redis client."""
        if self._redis_client is None:
            redis_client = Redis(connection_pool=self.redis_conn_pool)

            self._redis_client = redis_client

            self._logger.debug(
                "[%s]: Initialized Redis client: %s", self.__name__, self._redis_client
            )

        return self._redis_client

    @property
    def redis_conn_pool(self) -> ConnectionPool:
        """Provide an instance of Redis connection pool."""
        if self._redis_conn_pool is None:
            if self._config["graph_redis_pool_block"]:
                pool_class: Callable = BlockingConnectionPool
            else:
                pool_class = ConnectionPool

            if self._config["graph_redis_pool_gevent_queue"]:
                redis_conn_pool = pool_class().from_url(
                    self._config["graph_redis_url"],
                    decode_components=True,
                    max_connections=self._config["graph_redis_pool_max_connections"],
                    timeout=self._config["graph_redis_pool_timeout"],
                    queue_class=gevent.queue.LifoQueue,
                )

            else:
                redis_conn_pool = pool_class().from_url(
                    self._config["graph_redis_url"],
                    decode_components=True,
                    max_connections=self._config["graph_redis_pool_max_connections"],
                    timeout=self._config["graph_redis_pool_timeout"],
                )

            self._redis_conn_pool = redis_conn_pool

            self._logger.debug(
                "[%s]: Initialized Redis connection pool: %s",
                self.__name__,
                self._redis_conn_pool,
            )

        return self._redis_conn_pool

    def redis_rm_queue(self) -> bool:
        """Delete Redis queue storing data records.

        Returns
        -------
        bool
            Flag indicating success or failure of the operation.

        """
        redis_client: Redis = self.redis_client

        queue_type: str = self._config["graph_queue_type"]
        queue_key: str = self._config["graph_queue_key"]

        try:
            redis_client.delete(queue_key)

        except RedisError as e:
            result: bool = False
            self._logger.exception(  # noqa: G200
                "Exception deleting Redis key: %s", str(e)
            )

        else:
            result = True
            self._logger.info("Cleared %s key '%s'", queue_type.upper(), queue_key)

        return result

    def task_fetch_slice(
        self, slice_start: datetime = None, slice_end: datetime = None
    ) -> MsGraphResponse:
        """Fetch a time slice of records.

        Request time-domain data slice ``[slice_start - slice_end]``

        Parameters
        ----------
        slice_start
            Beginning of the time-domain data slice.

        slice_end
            End of the time-domain data slice.

        """
        result = self.graph.get_signins(
            timestamp_start=slice_start,
            timestamp_end=slice_end,
            page_size=self._config["graph_page_size"],
        )

        return result

    def task_get_time_slices(
        self, timestamp: datetime = None
    ) -> List[Tuple[datetime, datetime]]:
        """Calculate time slices from the point in time.

        Based on available configuration, generates a series of consecutive
        time slices (streams) going back in time from ``timestamp``.

        Parameters
        ----------
        timestamp
            Point in time from which to calculate time slices. Microseconds are
            zeroed and ``timestamp`` is rounded up to a second. If not defined,
            uses current time.

        Note
        ----
        Following ``_config`` options influence the result:

        * ``timelag`` - seconds to shift back from ``timestamp`` adjusting
          the whole time-frame for the series.
        * ``streams`` - Number of time slices to generate.
        * ``stream_frame`` - Size of each time slice in seconds.


        So, with the ``timestamp=...-07T22:02:53.123``, ``timelag=60``,
        ``streams=3`` and ``stream_frame=10`` following series is generated:

        .. code-block:: text

            1. [...-07T22:01:44 - ...-07T22:01:53]
            2. [...-07T22:01:34 - ...-07T22:01:43]
            3. [...-07T22:01:24 - ...-07T22:01:33]

        """
        total_streams: int = self._config["graph_streams"]

        t_now: datetime = (
            timestamp.replace(microsecond=0)
            if timestamp is not None
            else datetime.utcnow().replace(microsecond=0)
        )

        t_lag: timedelta = timedelta(seconds=self._config["graph_timelag"])
        t_sec: timedelta = timedelta(seconds=1)
        t_delta: timedelta = timedelta(seconds=self._config["graph_stream_frame"])

        frame_end: datetime = t_now - t_lag - t_sec
        frame_start: datetime = frame_end + t_sec - t_delta * total_streams

        self._logger.info(
            "Split [%s - %s] into %s slices",
            frame_start.isoformat(),
            frame_end.isoformat(),
            total_streams,
        )

        result: List[Tuple[datetime, datetime]] = []

        for i in range(total_streams):
            slice_start: datetime = frame_end + t_sec - t_delta * (i + 1)
            slice_end: datetime = frame_end - t_delta * i

            result.append((slice_start, slice_end))

        return result

    def task_records_to_log(self, records: List[Any]) -> None:
        """Push records to log.

        Output ``records`` in the log.

        Parameters
        ----------
        records
            List of records to queue.

        """
        for r in records:
            self._logger.info(
                "[%s]: %s - %s - %s/%s",
                r["createdDateTime"],
                r["userPrincipalName"],
                r["ipAddress"],
                r["location"]["countryOrRegion"],
                r["location"]["city"],
            )

    def task_redis_push_single(
        self, records: List[Any], push_mode: str = "pipe"
    ) -> bool:
        """Push records to Redis in a single batch.

        Note
        ----
        See the note for :meth:`task_redis_push_multi_spawn` for detailed explanation on
        parameter ``push_mode``.

        Parameters
        ----------
        records
            List of records to queue.

        push_mode
            Specifies the data transfer strategy to use.

        Returns
        -------
        bool
            Flag indicating success or failure of the operation

        """
        result: bool = False

        push_method = getattr(self, "_records_to_redis_{}".format(push_mode))

        result = push_method(records=records)

        return result

    def task_redis_push_multi_spawn(
        self, records: List[Any], push_mode: str = "pipe"
    ) -> bool:
        """Push records to Redis in parallel.

        Split ``records`` list into smaller data sets to be pushed to Redis
        with multiple Greenlets.

        Note
        ----
        Parameter ``push_mode`` defines which data transfer strategy to use
        by providing the suffix for specific ``_records_to_redis_*`` method
        to be called. Currently accepts ``naive`` or ``pipe``.

        Parameters
        ----------
        records
            List of records to store in Redis.

        push_mode
            Specifies the data transfer strategy to use.

        Returns
        -------
        bool
            Flag indicating success or failure of the operation

        """
        # noqa: D202
        def chunks(l: List, n: int):
            """Yield successive n-sized chunks from l."""
            for i in range(0, len(l), n):
                yield l[i : i + n]  # noqa: E203

        result: bool = False
        batch_size: int = 0
        records_len: int = len(records)
        greenlets_count: int = self._config["graph_greenlets_count"]

        if records_len > greenlets_count:
            batch_size = (((records_len << 1) // greenlets_count) + 1) >> 1

        elif records_len > 0:
            batch_size = records_len

        if records_len:
            greenlets: Group = Group()

            # See https://docs.python.org/3/library/functools.html#functools.partial
            redis_push_func_partial: Callable = partial(
                getattr(self, "_records_to_redis_{}".format(push_mode))
            )

            greenlet_list: List = []

            for batch in chunks(records, batch_size):
                greenlet_list.append(
                    greenlets.spawn(redis_push_func_partial, records=batch)
                )

            greenlets.join(raise_error=True)

            greenlet_results = [g.value for g in greenlet_list]

            self._logger.debug(
                "%s Greenlets spawned: %s", len(greenlet_results), greenlet_results
            )

            result = False if False in greenlet_results else True

        self._logger.debug("Summary result: %s", result)

        return result

    def task_redis_push_multi_imap(
        self, records: List[Any], push_mode: str = "pipe"
    ) -> bool:
        """Push records to Redis in parallel.

        Split ``records`` list into smaller data sets to be pushed to Redis
        with multiple Greenlets. Parameter ``push_mode`` defines which data
        transfer strategy to use.

        Note
        ----
        See the note for :meth:`task_redis_push_multi_spawn` for detailed explanation on
        parameter ``push_mode``.

        Parameters
        ----------
        records
            List of records to store in Redis.

        push_mode
            Specifies the data transfer strategy to use.

        Returns
        -------
        bool
            Flag indicating success or failure of the operation

        """
        # noqa: D202
        def chunks(l: List, n: int):
            """Yield successive n-sized chunks from l."""
            for i in range(0, len(l), n):
                yield l[i : i + n]  # noqa: E203

        result: bool = False
        batch_size: int = 0
        records_len: int = len(records)
        greenlets_count: int = self._config["graph_greenlets_count"]

        if records_len > greenlets_count:
            batch_size = (((records_len << 1) // greenlets_count) + 1) >> 1

        elif records_len > 0:
            batch_size = records_len

        if batch_size:
            greenlets: Group = Group()

            redis_push_func_partial: Callable = partial(
                getattr(self, "_records_to_redis_{}".format(push_mode))
            )

            greenlet_results: List = []

            for g in greenlets.imap_unordered(
                redis_push_func_partial, chunks(records, batch_size)
            ):
                greenlet_results.append(g)

            self._logger.debug(
                "%s Greenlets returned: %s", len(greenlet_results), greenlet_results
            )

            result = False if False in greenlet_results else True

        self._logger.debug("Summary result: %s", result)

        return result
