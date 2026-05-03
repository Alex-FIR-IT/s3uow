import pytest


@pytest.mark.asyncio
async def test_get_non_existing_returns_empty(uow_cls, text_files):
    async with uow_cls() as uow:
        result = await uow.user_files.get(text_files[0].filename)

        assert len(result) == 0


@pytest.mark.asyncio
async def test_put_and_get(uow_cls, text_files):
    async with uow_cls() as uow:
        await uow.user_files.put(*text_files)

        result = await uow.user_files.get(text_files[0].filename)

        assert len(result) == 1
        assert result[0].data == text_files[0].data

        result2 = await uow.user_files.get(text_files[1].filename)

        assert len(result2) == 1
        assert result2[0].data == text_files[1].data


@pytest.mark.asyncio
async def test_get_several_files_at_once(uow_cls, text_files):
    async with uow_cls() as uow:
        await uow.user_files.put(*text_files)

        result = await uow.user_files.get(
            text_files[0].filename,
            text_files[1].filename,
        )
        assert len(result) == 2
        assert result[0].data == text_files[0].data
        assert result[1].data == text_files[1].data

        # changing order of the filepaths in get method
        result = await uow.user_files.get(
            text_files[1].filename,
            text_files[0].filename,
        )
        assert len(result) == 2
        assert result[0].data == text_files[1].data
        assert result[1].data == text_files[0].data


@pytest.mark.asyncio
async def test_get_without_filepaths(uow_cls, text_files):
    async with uow_cls() as uow:
        await uow.user_files.put(*text_files)

        result = await uow.user_files.get()

        assert len(result) == 0
