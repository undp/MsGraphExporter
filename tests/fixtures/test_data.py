# -*- coding: utf-8 -*-
"""Module defines a fixture for data set to benchmark with."""
import json

import pytest


@pytest.fixture(
    scope="session",
    params=[
        {
            "file": "instance/data/data_benchmark.json",
            "size": 10000
            #
        }
    ],
    ids=[
        "10000"
        #
    ],
)
def test_data(request, logger):
    """Provide test data for benchmark."""
    with open(request.param["file"], "r") as data_file:
        data = json.load(data_file)

    data_set = data[: request.param["size"]]

    logger.info(
        "Provide fixture: Dataset with %s out of %s records", len(data_set), len(data)
    )

    yield data_set
