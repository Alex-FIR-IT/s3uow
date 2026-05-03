import asyncio

import pytest

from fennflow.backends.abstract.exceptions import RecordAlreadyExistsException


@pytest.mark.asyncio
async def test_put_same_file_twice_raises(uow_cls, text_files):
    async with uow_cls() as uow:
        await uow.user_files.at("user/").put(text_files[0])
        with pytest.raises(RecordAlreadyExistsException):
            await uow.user_files.at("user/").put(text_files[0])

    async with uow_cls() as uow:
        with pytest.raises(RecordAlreadyExistsException):
            await uow.user_files.at("user/").put(text_files[0])


@pytest.mark.asyncio
async def test_put_same_file_twice_in_different_sessions_raises(uow_cls, text_files):
    async with uow_cls() as uow:
        await uow.user_files.at("user/").put(text_files[0])

    async with uow_cls() as uow:
        with pytest.raises(RecordAlreadyExistsException):
            await uow.user_files.at("user/").put(text_files[0])


@pytest.mark.asyncio
async def test_concurrent_put_same_file_raises(uow_cls, text_files):
    # two UoWs trying to put the same filepath simultaneously
    # one should win, one should raise
    async with uow_cls() as uow1, uow_cls() as uow2:
        results = await asyncio.gather(
            uow1.user_files.at("user/").put(text_files[0]),
            uow2.user_files.at("user/").put(text_files[0]),
            return_exceptions=True,
        )
        assert any(isinstance(r, RecordAlreadyExistsException) for r in results)

    async with uow_cls() as uow:
        assert len(uow.backend.storage["user_files"]) == 1


@pytest.mark.asyncio
async def test_put_empty_files_list(uow_cls):
    async with uow_cls() as uow:
        await uow.user_files.at("user/").put()  # no files


@pytest.mark.asyncio
async def test_put_multiple_files(uow_cls, text_files):
    async with uow_cls() as uow:
        await uow.user_files.at("user/").put(*text_files)

        for file in text_files:
            result = await uow.user_files.at("user/").get(file.filename)
            assert result.media[0].data == file.data
