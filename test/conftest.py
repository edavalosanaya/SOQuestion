# References
# [loguru docs on pytest](https://loguru.readthedocs.io/en/stable/resources/migration.html#making-things-work-with-pytest-and-caplog)

import pytest
from loguru import logger
from _pytest.logging import LogCaptureFixture

@pytest.fixture
def caplog(caplog: LogCaptureFixture):
    handler_id = logger.add(caplog.handler, format="{message}")
    yield caplog
    logger.remove(handler_id)
