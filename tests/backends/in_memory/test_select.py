import datetime
import uuid

import pytest

from fennflow import ConfigDict, UnitOfWork
from fennflow._datetime import AwareDatetime, now
from fennflow._operations.dto import OperationRecord
from fennflow._operations.enums import OperationStatusEnum, OperationTypeEnum
from fennflow._sentinel import OMIT
from fennflow.backends import InMemoryBackendConfig
from fennflow.connectors import InMemoryConnectorConfig
from fennflow.files import TextContent
from fennflow.repositories import (
    DeleteRepository,
    GetRepository,
    PutRepository,
    RepoField,
)


class UserFiles(
    PutRepository,
    DeleteRepository,
    GetRepository,
):
    pass


@pytest.fixture
def now_dt() -> AwareDatetime:
    return now()


@pytest.fixture
def uow_cls():
    class InMemoryUOW(UnitOfWork):
        user_files = RepoField(UserFiles, namespace="user_files")
        config = ConfigDict(
            backend=InMemoryBackendConfig(),
            connector=InMemoryConnectorConfig(),
        )

    return InMemoryUOW


def make_files(*names):
    return [TextContent.from_content("content", filename=name) for name in names]


def make_record(**kwargs) -> OperationRecord:
    defaults = {
        "session_id": uuid.uuid4(),
        "storage_path": "folder1/file.txt",
        "repo_extra": {},
        "operation_type": OperationTypeEnum.PUT,
        "context": {},
        "status": OperationStatusEnum.PENDING,
    }
    defaults.update(kwargs)
    return OperationRecord(**defaults)


def inject(uow, storage_path: str, record: OperationRecord) -> None:
    uow.backend._storage[uow.backend._config.namespace][storage_path] = record


# --- status ---


@pytest.mark.asyncio
async def test_status_pending_before_commit(uow_cls):
    async with uow_cls() as uow:
        await uow.user_files.at("folder1/").put(TextContent.from_content("Hello"))

        page = await uow.backend.select(status=OperationStatusEnum.PENDING)
        assert len(page.operations) == 1
        assert page.operations[0].status == OperationStatusEnum.PENDING


@pytest.mark.asyncio
async def test_status_uploaded_after_commit(uow_cls):
    async with uow_cls() as uow:
        await uow.user_files.at("folder1/").put(TextContent.from_content("Hello"))
        await uow.commit()

        page = await uow.backend.select(status=OperationStatusEnum.UPLOADED)
        assert len(page.operations) == 1
        assert page.operations[0].status == OperationStatusEnum.UPLOADED


# --- prefix ---


@pytest.mark.asyncio
async def test_prefix_filter(uow_cls):
    async with uow_cls() as uow:
        await uow.user_files.at("folder1/").put(TextContent.from_content("a"))
        await uow.user_files.at("folder2/").put(TextContent.from_content("b"))

        page = await uow.backend.select(prefix="folder1/")
        assert len(page.operations) == 1
        assert page.operations[0].storage_path.startswith("folder1/")


# --- combined filters ---


@pytest.mark.asyncio
async def test_prefix_and_status_combined(uow_cls):
    async with uow_cls() as uow:
        await uow.user_files.at("folder1/").put(TextContent.from_content("a"))
        await uow.user_files.at("folder2/").put(TextContent.from_content("b"))
        await uow.commit()
        await uow.user_files.at("folder1/").put(TextContent.from_content("c"))

        page = await uow.backend.select(
            prefix="folder1/", status=OperationStatusEnum.PENDING
        )
        assert len(page.operations) == 1
        assert page.operations[0].storage_path.startswith("folder1/")
        assert page.operations[0].status == OperationStatusEnum.PENDING


# --- session_id ---


@pytest.mark.asyncio
async def test_session_id_filter(uow_cls):
    async with uow_cls() as uow:
        session_a = uuid.uuid4()
        session_b = uuid.uuid4()
        inject(
            uow,
            "folder1/a.txt",
            make_record(storage_path="folder1/a.txt", session_id=session_a),
        )
        inject(
            uow,
            "folder1/b.txt",
            make_record(storage_path="folder1/b.txt", session_id=session_b),
        )

        page = await uow.backend.select(session_id=session_a)
        assert len(page.operations) == 1
        assert page.operations[0].session_id == session_a


# --- is_expired ---


@pytest.mark.asyncio
async def test_is_expired(uow_cls):
    async with uow_cls() as uow:
        expired = make_record(
            storage_path="folder1/expired.txt",
            expired_at=datetime.datetime.now(tz=datetime.UTC)
            - datetime.timedelta(seconds=1),
        )
        active = make_record(
            storage_path="folder1/active.txt",
            expired_at=datetime.datetime.now(tz=datetime.UTC)
            + datetime.timedelta(seconds=60),
        )
        inject(uow, "folder1/expired.txt", expired)
        inject(uow, "folder1/active.txt", active)

        page = await uow.backend.select(is_expired=True)
        assert all(r.storage_path == "folder1/expired.txt" for r in page.operations)
        page2 = await uow.backend.select(is_expired=False)
        assert all(r.storage_path == "folder1/active.txt" for r in page2.operations)


# --- ordering ---


@pytest.mark.asyncio
async def test_results_ordered_by_created_at(uow_cls):
    async with uow_cls() as uow:
        for i in range(4):
            await uow.user_files.at("folder1/").put(
                TextContent.from_content(f"file{i}")
            )

        page = await uow.backend.select(prefix="folder1/")
        dates = [r.created_at for r in page.operations]
        assert dates == sorted(dates)


# --- pagination ---


@pytest.mark.asyncio
async def test_pagination_limit(uow_cls):
    async with uow_cls() as uow:
        for i in range(5):
            await uow.user_files.at("folder1/").put(
                TextContent.from_content(f"file{i}")
            )

        page = await uow.backend.select(prefix="folder1/", limit=2)
        assert len(page.operations) == 2
        assert page.continuation_token is not None


@pytest.mark.asyncio
async def test_pagination_continuation_token_no_overlap(uow_cls):
    async with uow_cls() as uow:
        for i in range(5):
            await uow.user_files.at("folder1/").put(
                TextContent.from_content(f"file{i}")
            )

        page1 = await uow.backend.select(prefix="folder1/", limit=2)
        page2 = await uow.backend.select(
            prefix="folder1/", limit=2, continuation_token=page1.continuation_token
        )

        ids1 = {r.operation_id for r in page1.operations}
        ids2 = {r.operation_id for r in page2.operations}
        assert ids1.isdisjoint(ids2)


@pytest.mark.asyncio
async def test_pagination_all_pages_cover_all_records(uow_cls):
    async with uow_cls() as uow:
        for i in range(5):
            await uow.user_files.at("folder1/").put(
                TextContent.from_content(f"file{i}")
            )

        all_ids = set()
        token = OMIT
        while True:
            page = await uow.backend.select(
                prefix="folder1/", limit=2, continuation_token=token
            )
            all_ids.update(r.operation_id for r in page.operations)
            if page.continuation_token is None:
                break
            token = page.continuation_token

        assert len(all_ids) == 5


@pytest.mark.asyncio
async def test_limit_equals_total_records_no_token(uow_cls):
    async with uow_cls() as uow:
        for i in range(3):
            await uow.user_files.at("folder1/").put(
                TextContent.from_content(f"file{i}")
            )

        page = await uow.backend.select(prefix="folder1/", limit=3)
        assert len(page.operations) == 3
        assert page.continuation_token is None


@pytest.mark.asyncio
async def test_continuation_token_on_last_record_returns_no_token(uow_cls):
    async with uow_cls() as uow:
        for i in range(3):
            await uow.user_files.at("folder1/").put(
                TextContent.from_content(f"file{i}")
            )

        page1 = await uow.backend.select(prefix="folder1/", limit=2)
        page2 = await uow.backend.select(
            prefix="folder1/", limit=2, continuation_token=page1.continuation_token
        )
        assert page2.continuation_token is None


@pytest.mark.asyncio
async def test_pagination_token_works_after_status_change(uow_cls):
    async with uow_cls() as uow:
        for i in range(4):
            await uow.user_files.at("folder1/").put(
                TextContent.from_content(f"file{i}")
            )

        page1 = await uow.backend.select(status=OperationStatusEnum.PENDING, limit=2)
        await uow.commit()

        page2 = await uow.backend.select(
            status=OperationStatusEnum.UPLOADED,
            limit=2,
            continuation_token=page1.continuation_token,
        )
        assert len(page2.operations) == 2


# --- empty ---


@pytest.mark.asyncio
async def test_no_results(uow_cls):
    async with uow_cls() as uow:
        page = await uow.backend.select(prefix="nonexistent/")
        assert page.operations == ()
        assert page.continuation_token is None
