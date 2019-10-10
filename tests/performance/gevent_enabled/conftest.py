# -*- coding: utf-8 -*-
"""Module performs gevent monkey patching affecting all tests in the package."""
# fmt: off
from gevent.monkey import patch_all; patch_all()  # noqa: E702
# fmt: on
