# -*- coding: utf-8 -*-
"""Module defines common test fixtures."""
from logging import getLogger

import pytest


@pytest.fixture(scope="session")
def logger():
    """Provide logger instance."""
    logger = getLogger(__name__)

    return logger
