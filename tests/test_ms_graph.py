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
        "cache_parameter", [True, False], ids=["cache", "no_cache"]
    )
    @pytest.mark.parametrize(
        "user_id_parameter", ["user@undp.org", None], ids=["user", "no_user"]
    )
    @pytest.mark.parametrize("page_size_parameter", [10], ids=["page_10"])
    @pytest.mark.parametrize(
        "timeframe_parameter",
        [
            {
                "timestamp_start": datetime(2019, 8, 24, 20, 0, 0),
                "timestamp_end": datetime(2019, 8, 24, 20, 0, 15),
            }
        ],
        ids=["timeframe_short"],
    )
    @pytest.mark.usefixtures("graph_real")
    def test_get_signins(
        self,
        logger,
        graph_real,
        user_id_parameter,
        timeframe_parameter,
        page_size_parameter,
        cache_parameter,
    ):
        """Test getting Azure AD signin data."""
        signins = graph_real.get_signins(
            user_id=user_id_parameter,
            timestamp_start=timeframe_parameter["timestamp_start"],
            timestamp_end=timeframe_parameter["timestamp_end"],
            page_size=page_size_parameter,
            cache_enabled=cache_parameter,
        )

        for i in range(1, 3):
            logger.info("Iterating through results: %s pass", i)

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
