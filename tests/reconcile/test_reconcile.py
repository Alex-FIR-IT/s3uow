import pytest

from fennflow._operations.enums import OperationStatusEnum
from fennflow.connectors import InMemoryConnector


@pytest.mark.asyncio
async def test_reconcile_on_empty_connector(uow_cls):
    async with uow_cls() as uow:
        response = await uow.user_files.list()

        assert len(response) == 0


@pytest.mark.asyncio
async def test_reconcile_on_non_empty_connector(uow_cls, text_files):

    for text_file in text_files:
        InMemoryConnector._storage[uow_cls.user_files.repo_extra["namespace"]][
            text_file.filename
        ] = text_file

    async with uow_cls() as uow:
        response = await uow.user_files.list()

        assert len(response) != 0

        files = []
        for filepath in response:
            response = await uow.user_files.get(filepath)
            files.extend(response)

        assert sorted(files) == sorted(text_files)
