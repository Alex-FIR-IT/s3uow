import pytest


@pytest.mark.asyncio
async def test_auto_commit(uow_cls, text_files):
    async with uow_cls() as uow:
        await uow.user_files.at("user/").put(*text_files)

    async with uow_cls() as uow:
        result = await uow.user_files.at("user/").get(text_files[0].filename)

        assert len(result) == 1

    async with uow_cls() as uow:
        result = await uow.user_files.at("user/").delete(text_files[0].filename)
        result = await uow.user_files.at("user/").get(text_files[0].filename)
        assert len(result) == 0


@pytest.mark.asyncio
async def test_manual_commit(uow_cls, text_files):
    async with uow_cls(auto_commit=False) as uow:
        await uow.user_files.at("user/").put(*text_files)
        await uow.commit()

    async with uow_cls() as uow:
        result = await uow.user_files.at("user/").get(text_files[0].filename)

        assert len(result.media) == 1


@pytest.mark.asyncio
async def test_auto_commit_false(uow_cls, text_files):
    async with uow_cls(auto_commit=False) as uow:
        await uow.user_files.at("user/").put(*text_files)

    async with uow_cls() as uow:
        result = await uow.user_files.at("user/").get(text_files[0].filename)

        assert len(result.media) == 0


@pytest.mark.asyncio
async def test_commit_empty_transaction(uow_cls):
    # committing with no operations should not raise
    async with uow_cls() as uow:
        await uow.commit()


@pytest.mark.asyncio
async def test_backend_marks_done_after_commit(uow_cls, text_files):
    async with uow_cls() as uow:
        await uow.user_files.at("user/").put(*text_files)

    # inspect backend directly
    for file in text_files:
        record = await uow.backend.get(
            filepath=f"user/{file.filename}", namespace="user_files"
        )
        assert record.status == "uploaded"
