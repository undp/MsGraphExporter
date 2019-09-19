# -*- coding: utf-8 -*-
"""Module defines a fixture for :class:`~ms_graph_exporter.ms_graph.api.MsGraph`."""
from os import environ

import pytest

from ms_graph_exporter.ms_graph.api import MsGraph


@pytest.fixture(scope="session")
def graph_real(logger):
    """Provide MsGraph instance with access to actual MS Graph API."""
    try:
        _graph = MsGraph(
            client_id=environ.get("GRAPH_CLIENT_ID", "undefined"),
            client_secret=environ.get("GRAPH_CLIENT_SECRET", "undefined"),
            tenant=environ.get("GRAPH_TENANT", "undefined"),
        )

    except Exception:
        logger.exception("[MsGraph]: Fixture not properly instantiated")
        yield None

    else:
        logger.info("%s: Provide 'graph_real' fixture", _graph)
        yield _graph

    finally:
        logger.info("%s: Destroy 'graph_real' fixture", _graph)
