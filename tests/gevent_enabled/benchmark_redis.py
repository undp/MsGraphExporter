"""Module contains performance testing scenarios."""
import pytest

pytest_plugins = ["tests.fixtures.test_data", "tests.fixtures.graph_api_task"]


@pytest.mark.benchmark(group="redis")
@pytest.mark.usefixtures("logger")
@pytest.mark.usefixtures("graph_api_task")
@pytest.mark.usefixtures("test_data")
class TestBenchmark:
    """Performance test suite using MS Graph API task base class."""

    @pytest.mark.parametrize("target_suffix", ["multi_spawn", "multi_imap", "single"])
    @pytest.mark.parametrize(
        "push_mode", ["pipe"]  # add "naive" push_mode for full coverage (slow!)
    )
    def test_redis_push(
        self, benchmark, graph_api_task, logger, push_mode, target_suffix, test_data
    ):
        """Benchmark routine to evaluate pushing records to Redis."""
        import gevent.socket
        import socket

        logger.info(
            "Gevent monkey patching is %s",
            "ENABLED" if socket.socket is gevent.socket.socket else "DISABLED",
        )

        assert socket.socket is gevent.socket.socket  # noqa

        logger.info("Start benchmark")

        result = benchmark.pedantic(
            target=getattr(graph_api_task, "task_redis_push_{}".format(target_suffix)),
            args=[test_data, push_mode],
            iterations=1,
            rounds=5,
        )

        logger.info("Finish benchmark")

        graph_api_task.redis_rm_queue()

        assert result == True  # noqa
