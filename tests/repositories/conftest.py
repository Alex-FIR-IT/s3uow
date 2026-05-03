import pytest

from fennflow.connectors import InMemoryConnector


@pytest.fixture
def reset_put_count():
    InMemoryConnector._put_count = 0
    yield
    InMemoryConnector._put_count = 0
