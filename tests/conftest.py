# -*- coding: utf-8 -*-
"""Module defines common test fixtures."""
from logging import getLogger

# fmt: off
from gevent.monkey import patch_all; patch_all()  # noqa: E702
# fmt: on

import pytest


@pytest.fixture(scope="session")
def logger():
    """Provide logger instance."""
    logger = getLogger(__name__)

    return logger
