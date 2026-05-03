import pytest


@pytest.mark.asyncio
async def test_delete_removes_file(uow_cls, text_files):
    async with uow_cls() as uow:
        await uow.user_files.at("user/").put(*text_files)

        await uow.user_files.at("user/").delete(text_files[0].filename)

        result = await uow.user_files.at("user/").get(text_files[0].filename)
        assert len(result) == 0

        result = await uow.user_files.at("user/").get(text_files[1].filename)
        assert len(result) == 1
