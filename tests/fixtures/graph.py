# -*- coding: utf-8 -*-
"""Module defines a fixture for :class:`~ms_graph_exporter.ms_graph.api.MsGraph`."""
import pytest

from ms_graph_exporter.ms_graph.api import MsGraph


@pytest.fixture(scope="session")
def graph_real(request, variables, logger):
    """Provide MsGraph instance with access to actual MS Graph API."""
    try:
        _graph = MsGraph(
            # REFACTOR:20190918:01
            #   get sensitive values from ENV, instead of `variables` fixture
            client_id=variables.get("client_id"),
            client_secret=variables.get("client_secret"),
            tenant=variables.get("tenant"),
        )

    except Exception:
        logger.exception("[MsGraph]: Fixture not properly instantiated")
        yield None

    else:
        logger.info("%s: Provide 'graph_real' fixture", _graph)
        yield _graph

    finally:
        logger.info("%s: Destroy 'graph_real' fixture", _graph)
