import pytest

from fennflow.connectors import InMemoryConnector


@pytest.mark.asyncio
async def test_get_non_existing_returns_empty(uow_cls, text_files):
    async with uow_cls() as uow:
        result = await uow.user_files.get(text_files[0].filename)

        assert len(result) == 0


@pytest.mark.asyncio
async def test_put_and_get(uow_cls, text_files):
    async with uow_cls() as uow:
        await uow.user_files.create(*text_files)

        result = await uow.user_files.get(text_files[0].filename)

        assert len(result) == 1
        assert result[0].data == text_files[0].data

        result2 = await uow.user_files.get(text_files[1].filename)

        assert len(result2) == 1
        assert result2[0].data == text_files[1].data


@pytest.mark.asyncio
async def test_get_several_files_at_once(uow_cls, text_files):
    async with uow_cls() as uow:
        await uow.user_files.create(*text_files)

        result = await uow.user_files.get(
            text_files[0].filename,
            text_files[1].filename,
        )
        assert len(result) == 2
        assert result[0].data == text_files[0].data
        assert result[1].data == text_files[1].data

        # changing order of the storage_paths in get method
        result = await uow.user_files.get(
            text_files[1].filename,
            text_files[0].filename,
        )
        assert len(result) == 2
        assert result[0].data == text_files[1].data
        assert result[1].data == text_files[0].data


@pytest.mark.asyncio
async def test_get_without_storage_paths(uow_cls, text_files):
    async with uow_cls() as uow:
        await uow.user_files.create(*text_files)

        result = await uow.user_files.get()

        assert len(result) == 0


@pytest.mark.asyncio
async def test_not_calling_connector_for_not_uploaded(
    uow_cls,
    text_files,
    monkeypatch,
):
    get_count = 0
    original_get = InMemoryConnector.get

    async def count_get(*args, **kwargs):
        nonlocal get_count

        get_count += 1
        return await original_get(*args, **kwargs)

    monkeypatch.setattr(InMemoryConnector, "get", count_get)

    async with uow_cls() as uow:
        response = await uow.user_files.get(text_files[0].filename)
        assert len(response) == 0
        assert get_count == 0

        await uow.user_files.create(*text_files)

        response = await uow.user_files.get(text_files[0].filename)

        assert len(response) == 1
        assert get_count == 1

        await uow.commit()

        response = await uow.user_files.get(text_files[0].filename)

        assert len(response) == 1
        assert get_count == 2

        response = await uow.user_files.delete(text_files[0].filename)

        response = await uow.user_files.get(text_files[0].filename)

        assert len(response) == 0
        assert get_count == 2

        await uow.rollback()

        response = await uow.user_files.get(text_files[0].filename)

        assert len(response) == 1
        assert get_count == 3

        response = await uow.user_files.get(text_files[1].storage_path)

        assert len(response) == 1
        assert get_count == 4
