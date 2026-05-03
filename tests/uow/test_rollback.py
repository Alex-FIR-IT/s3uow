import pytest


@pytest.mark.asyncio
async def test_manual_rollback(uow_cls, text_files):
    async with uow_cls() as uow:
        await uow.user_files.at("user/").put(*text_files)
        await uow.rollback()

    async with uow_cls() as uow:
        result = await uow.user_files.at("user/").get(text_files[0].filename)

        assert result.media == ()


@pytest.mark.asyncio
async def test_rollback_on_exception(uow_cls, text_files):
    try:
        async with uow_cls() as uow:
            await uow.user_files.at("user/").put(*text_files)

            raise RuntimeError("boom")

    except RuntimeError:
        pass

    async with uow_cls() as uow:
        result = await uow.user_files.at("user/").get(text_files[0].filename)

        assert result.media == ()


@pytest.mark.asyncio
async def test_backend_marks_failed_after_rollback(uow_cls, text_files):
    try:
        async with uow_cls() as uow:
            await uow.user_files.at("user/").put(*text_files)
            raise RuntimeError("boom")
    except RuntimeError:
        pass

    for file in text_files:
        record = await uow.backend.get(
            filepath=f"user/{file.filename}", namespace="user_files"
        )
        assert record.status == "failed"
