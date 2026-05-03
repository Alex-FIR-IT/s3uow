import pytest

from fennflow._operations.enums import OperationTypeEnum
from fennflow.connectors import InMemoryConnector


@pytest.fixture
def reset_put_count():
    InMemoryConnector._put_count = 0
    yield
    InMemoryConnector._put_count = 0


@pytest.mark.asyncio
async def test_partial_put_failure_compensates_succeeded(
    uow_cls,
    text_files,
    monkeypatch,
    reset_put_count,
):
    assert len(text_files) >= 2

    put_count = 0
    original_put = InMemoryConnector.put

    async def failing_put(self, file, repo_extra, **extra):
        nonlocal put_count
        put_count += 1
        if put_count >= 2:
            raise RuntimeError(f"Simulated failure on: {file.filepath}")
        await original_put(self, file, repo_extra, **extra)

    monkeypatch.setattr(InMemoryConnector, "put", failing_put)

    with pytest.raises(RuntimeError, match="Simulated failure"):
        async with uow_cls() as uow:
            await uow.user_files.at("user/").put(*text_files)

    # verify failure actually happened
    assert put_count == 2, f"Expected 2 put attempts, got {put_count}"

    # file1 was uploaded but must have been compensated (deleted)
    async with uow_cls() as uow:
        result = await uow.user_files.at("user/").get(text_files[0].filename)
        assert result.media == (), "file1 should have been compensated"

    # file2 failed before upload, must not exist
    async with uow_cls() as uow:
        result = await uow.user_files.at("user/").get(text_files[1].filename)
        assert result.media == (), "file2 was never uploaded"


@pytest.mark.asyncio
async def test_partial_put_failure_compensates_deletes(
    uow_cls,
    text_files,
    monkeypatch,
):
    assert len(text_files) >= 2

    put_count = 0
    compensate_count = 0
    original_put = InMemoryConnector.put
    original_delete = InMemoryConnector.delete

    async def failing_put(self, file, repo_extra, **extra):
        nonlocal put_count
        put_count += 1
        if put_count >= 2:
            raise RuntimeError(f"Simulated failure on: {file.filepath}")
        await original_put(self, file, repo_extra, **extra)

    async def tracking_delete(self, filepath, repo_extra, **extra):
        nonlocal compensate_count
        compensate_count += 1
        await original_delete(self, filepath, repo_extra, **extra)

    monkeypatch.setattr(InMemoryConnector, "put", failing_put)
    monkeypatch.setattr(InMemoryConnector, "delete", tracking_delete)

    with pytest.raises(RuntimeError, match="Simulated failure"):
        async with uow_cls() as uow:
            await uow.user_files.at("user/").put(*text_files)

    # verify failure actually happened
    assert put_count == 2, f"Expected 2 put attempts, got {put_count}"

    assert compensate_count == 2
    # verify file1 is gone from connector storage directly
    assert ("user_files", text_files[0].filepath) not in InMemoryConnector.storage

    # verify file2 was never in connector storage
    assert ("user_files", text_files[1].filepath) not in InMemoryConnector.storage

    # checking statuses for files:

    async with uow_cls() as uow:
        operation1 = await uow.backend.get(
            text_files[0].filepath, namespace="user_files"
        )
        operation2 = await uow.backend.get(
            text_files[1].filepath, namespace="user_files"
        )

        assert operation1.is_failed is True
        assert operation2.is_failed is True


@pytest.mark.asyncio
async def test_file_recovery_after_deleting_on_rollback(
    uow_cls,
    text_files,
):
    async with uow_cls() as uow:
        await uow.user_files.at("user/").put(text_files[0])

    async with uow_cls(auto_commit=False) as uow:
        get_response = await uow.user_files.at("user/").get(text_files[0].filename)
        assert len(get_response) == 1, f"Expected 1 file, got {len(get_response)}"
        assert get_response[0].data == text_files[0].data

        await uow.user_files.at("user/").delete(text_files[0].filename)

        response = await uow.user_files.at("user/").get(text_files[0].filename)
        assert len(response) == 0

    async with uow_cls() as uow:
        response = await uow.user_files.at("user/").get(text_files[0].filename)
        assert len(response) == 1, f"Expected 1 file, got {len(response)}"
        assert response[0].data == text_files[0].data

        operation = await uow.backend.get(
            text_files[0].filepath, namespace="user_files"
        )

        assert operation.is_uploaded is True
