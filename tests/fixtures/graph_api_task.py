# -*- coding: utf-8 -*-
"""Module defines a fixture for data set to benchmark with."""
import pytest

from ms_graph_exporter.celery.graph_api_base import GraphApiTask


@pytest.fixture(
    scope="function",
    params=[
        #
        {
            #
            "max_connections": 15,
            "greenlets_count": 10,
            "graph_redis_pool_block": True,
        }
    ],
    ids=[
        #
        "10x"
    ],
)
def graph_api_task(request, logger):
    """Provide preconfigured instance of class:`GraphApiTask`.

    Fixture expect test configuration to reside in ``instance/app_config.yaml.``

    """
    task_base = GraphApiTask()

    task_base.config_update_from_file("instance/app_config.yaml")

    task_base.config_update(
        graph_redis_pool_max_connections=request.param["max_connections"],
        graph_greenlets_count=request.param["greenlets_count"],
        graph_redis_pool_block=request.param["graph_redis_pool_block"],
    )

    task_base.redis_rm_queue()

    logger.info("Provide fixture: GraphApiTask(%s)", request.param)

    yield task_base

    logger.info("Fixture cleanup.")
    task_base.redis_rm_queue()
