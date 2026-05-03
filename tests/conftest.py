import logging

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
import tracemalloc

import pytest

from fennflow import ConfigDict
from fennflow.backends import InMemoryBackend, InMemoryBackendConfig
from fennflow.connectors import InMemoryConnector, InMemoryConnectorConfig
from fennflow.files import TextContent
from fennflow.repositories import (
    DeleteRepository,
    GetRepository,
    PutRepository,
    RepoField,
)
from fennflow.uow import UnitOfWork

# 1. Запуск системы отслеживания
# snapshot_count — количество кадров стека, которые нужно сохранить (по умолчанию 1)
tracemalloc.start(10)


class UserFiles(
    PutRepository,
    DeleteRepository,
    GetRepository,
):
    pass


class TestUOW(UnitOfWork):
    user_files = RepoField(UserFiles, namespace="user_files")
    config = ConfigDict(
        backend=InMemoryBackendConfig(),
        connector=InMemoryConnectorConfig(),
    )


@pytest.fixture
def uow_cls():
    return TestUOW


@pytest.fixture
def text_files():
    return [
        TextContent.from_content("hello"),
        TextContent.from_content("world"),
    ]


@pytest.fixture(autouse=True)
def reset_inmemory_state():
    InMemoryBackend.drop_all()
    InMemoryConnector.drop_all()
