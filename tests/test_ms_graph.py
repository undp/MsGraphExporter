"""Module implements a functional test case with live MS Graph API endpoint."""
from datetime import datetime, timedelta

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
        "delta_parameter", [10, 30], ids=["delta_10s", "delta_30s"]
    )
    @pytest.mark.usefixtures("graph_real")
    def test_get_signins(
        self,
        cache_parameter,
        delta_parameter,
        graph_real,
        logger,
        page_size_parameter,
        user_id_parameter,
    ):
        """Test getting Azure AD signin data."""
        t_now = datetime.utcnow().replace(microsecond=0)

        t_lag = timedelta(seconds=120)
        t_sec = timedelta(seconds=1)
        t_delta = timedelta(seconds=delta_parameter)

        frame_end = t_now - t_lag - t_sec
        frame_start = frame_end + t_sec - t_delta

        signins = graph_real.get_signins(
            user_id=user_id_parameter,
            timestamp_start=frame_start,
            timestamp_end=frame_end,
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
