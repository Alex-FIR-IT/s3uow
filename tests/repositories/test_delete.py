import pytest

from fennflow.connectors import InMemoryConnector


@pytest.mark.asyncio
async def test_delete_removes_file(uow_cls, text_files):
    async with uow_cls() as uow:
        await uow.user_files.at("user/").create(*text_files)

        await uow.user_files.at("user/").delete(text_files[0].filename)

        result = await uow.user_files.at("user/").get(text_files[0].filename)
        assert len(result) == 0

        result = await uow.user_files.at("user/").get(text_files[1].filename)
        assert len(result) == 1


@pytest.mark.asyncio
async def test_delete_after_commit(uow_cls, text_files):
    async with uow_cls() as uow:
        await uow.user_files.at("user/").create(*text_files)
        await uow.commit()
        await uow.user_files.at("user/").delete(text_files[0].filename)

        result = await uow.user_files.at("user/").get(text_files[0].filename)
        assert len(result) == 0
        await uow.commit()
        result = await uow.user_files.at("user/").get(text_files[0].filename)
        assert len(result) == 0


@pytest.mark.asyncio
async def test_delete_not_calling_connector_for_status_deleted(
    uow_cls, text_files, monkeypatch
):
    delete_count = 0
    original_delete = InMemoryConnector.delete

    async def tracking_delete(self, storage_path, repo_extra, **extra):
        nonlocal delete_count
        delete_count += 1
        await original_delete(self, storage_path, repo_extra, **extra)

    monkeypatch.setattr(InMemoryConnector, "delete", tracking_delete)

    async with uow_cls() as uow:
        await uow.user_files.at("user/").create(*text_files)
        await uow.user_files.at("user/").delete(text_files[0].filename)
        assert delete_count == 1
        await uow.user_files.at("user/").delete(text_files[0].filename)
        assert delete_count == 1

        await uow.commit()
        assert (
            delete_count == 2
        )  # compensation deleted a tmp file, thus delete_count is incremented
        await uow.user_files.at("user/").delete(text_files[0].filename)
        assert delete_count == 2


@pytest.mark.asyncio
async def test_delete_several_times_and_rollback(uow_cls, text_files):
    file = text_files[0]
    async with uow_cls() as uow:
        response = await uow.user_files.create(file)
        await uow.commit()

        for _ in range(100):
            await uow.user_files.delete(file.filename)

        response = await uow.user_files.get(file.filename)
        assert len(response) == 0

        await uow.rollback()

        response = await uow.user_files.get(file.filename)
        assert len(response) == 1
        assert response[0].data == file.data
