"""Module implements a functional test case with live MS Graph API endpoint."""
from datetime import datetime

import pytest

pytest_plugins = ["tests.fixtures.graph"]


@pytest.mark.functional
@pytest.mark.usefixtures("logger")
class TestAppFunction:
    """Overall functional test case of :mod:`~ms_graph_exporter.ms_graph`.

    Relies on access to live MS API endpoint.
    """

    @pytest.mark.parametrize(
        "test_params",
        [
            {
                "user_id": "user@undp.org",
                "timestamp_start": datetime(2019, 8, 24, 20, 0, 0),
                "timestamp_end": datetime(2019, 8, 24, 20, 16, 12),
                "page_size": 50,
            },
            {
                "user_id": None,
                "timestamp_start": datetime(2019, 8, 24, 20, 0, 0),
                "timestamp_end": datetime(2019, 8, 24, 20, 0, 12),
                "page_size": 10,
            },
        ],
    )
    @pytest.mark.usefixtures("graph_real")
    def test_get_signins(self, caplog, logger, graph_real, test_params):
        """Test getting Azure AD signin data."""
        signins = graph_real.get_signins(
            user_id=test_params["user_id"],
            timestamp_start=test_params["timestamp_start"],
            timestamp_end=test_params["timestamp_end"],
            page_size=test_params["page_size"],
            cache_enabled=True,
        )

        for page in signins:
            for record in page:
                logger.info(
                    "%s: [%s]: %s - %s - %s/%s",
                    signins,
                    record["createdDateTime"],
                    record["userPrincipalName"],
                    record["ipAddress"],
                    record["location"]["countryOrRegion"],
                    record["location"]["city"],
                )
