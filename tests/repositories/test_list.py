import pytest

from fennflow._sentinel import OMIT
from fennflow.files import TextContent


@pytest.fixture
def text_files():
    return [TextContent.from_content(f"file{i}") for i in range(5)]


# --- visibility ---


@pytest.mark.asyncio
async def test_list_returns_empty_before_commit(uow_cls, text_files):
    async with uow_cls() as uow:
        await uow.user_files.at("folder1/").put(text_files[0])

        async with uow_cls() as other_uow:
            result = await other_uow.user_files.at("").list("folder1/")
            assert len(result) == 0


@pytest.mark.asyncio
async def test_list_returns_pending_within_same_session(uow_cls, text_files):
    async with uow_cls() as uow:
        await uow.user_files.at("folder1/").put(text_files[0])

        result = await uow.user_files.at("").list("folder1/")
        assert len(result) == 1


@pytest.mark.asyncio
async def test_list_returns_uploaded_after_commit(uow_cls, text_files):
    async with uow_cls() as uow:
        await uow.user_files.at("folder1/").put(text_files[0])
        await uow.commit()

        result = await uow.user_files.at("").list("folder1/")
        assert len(result) == 1


@pytest.mark.asyncio
async def test_list_uploaded_visible_to_other_session(uow_cls, text_files):
    async with uow_cls() as uow:
        await uow.user_files.at("folder1/").put(text_files[0])
        await uow.commit()

    async with uow_cls() as other_uow:
        result = await other_uow.user_files.at("").list("folder1/")
        assert len(result) == 1


# --- prefix ---


@pytest.mark.asyncio
async def test_list_filters_by_prefix(uow_cls, text_files):
    async with uow_cls() as uow:
        await uow.user_files.at("folder1/").put(text_files[0])
        await uow.user_files.at("folder2/").put(text_files[1])
        await uow.commit()

        result = await uow.user_files.at("").list("folder1/")
        assert len(result) == 1
        assert all(fp.startswith("folder1/") for fp in result)


# --- pagination ---


@pytest.mark.asyncio
async def test_list_pagination_limit(uow_cls, text_files):
    async with uow_cls() as uow:
        await uow.user_files.at("folder1/").put(*text_files)
        await uow.commit()

        result = await uow.user_files.at("").list("folder1/", limit=2)
        assert len(result) == 2
        assert result.continuation_token is not None


@pytest.mark.asyncio
async def test_list_pagination_no_overlap(uow_cls, text_files):
    async with uow_cls() as uow:
        await uow.user_files.at("folder1/").put(*text_files)
        await uow.commit()

        page1 = await uow.user_files.at("").list("folder1/", limit=2)
        page2 = await uow.user_files.at("").list(
            "folder1/",
            limit=2,
            continuation_token=page1.continuation_token,
        )

        assert set(page1.filepaths).isdisjoint(set(page2.filepaths))


@pytest.mark.asyncio
async def test_list_pagination_covers_all(uow_cls, text_files):
    async with uow_cls() as uow:
        await uow.user_files.at("folder1/").put(*text_files)
        await uow.commit()

        all_filepaths = set()
        token = OMIT
        while True:
            page = await uow.user_files.at("").list(
                "folder1/", limit=2, continuation_token=token
            )
            all_filepaths.update(page.filepaths)
            if page.continuation_token is None:
                break
            token = page.continuation_token

        assert len(all_filepaths) == len(text_files)


@pytest.mark.asyncio
async def test_list_limit_equals_total_no_token(uow_cls, text_files):
    async with uow_cls() as uow:
        await uow.user_files.at("folder1/").put(*text_files)
        await uow.commit()

        result = await uow.user_files.at("").list("folder1/", limit=len(text_files))
        assert len(result) == len(text_files)
        assert result.continuation_token is None


# --- empty ---


@pytest.mark.asyncio
async def test_list_empty_folder(uow_cls):
    async with uow_cls() as uow:
        result = await uow.user_files.at("").list("nonexistent/")
        assert len(result) == 0
        assert result.continuation_token is None


@pytest.mark.asyncio
async def test_list_does_not_return_deleted(uow_cls, text_files):
    async with uow_cls() as uow:
        await uow.user_files.at("folder1/").put(text_files[0])
        await uow.commit()
        await uow.user_files.at("folder1/").delete(text_files[0].filename)
        await uow.commit()

        result = await uow.user_files.at("").list("folder1/")
        assert len(result) == 0


@pytest.mark.asyncio
async def test_list_pending_from_other_session_not_visible(uow_cls, text_files):
    async with uow_cls() as session_a:
        await session_a.user_files.at("folder1/").put(text_files[0])  # not committed

        async with uow_cls() as session_b:
            result = await session_b.user_files.at("").list("folder1/")
            assert len(result) == 0


@pytest.mark.asyncio
async def test_list_partial_return_after_delete(uow_cls, text_files):
    async with uow_cls() as uow:
        await uow.user_files.at("folder1/").put(*text_files)
        await uow.commit()
        await uow.user_files.at("folder1/").delete(text_files[0].filename)
        result = await uow.user_files.at("folder1/").list()
        assert len(result) == 4

        await uow.commit()

        result = await uow.user_files.at("folder1/").list()
        assert len(result) == 4
