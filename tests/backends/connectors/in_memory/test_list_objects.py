import pytest

from fennflow._sentinel import OMIT
from fennflow.files.responses.list import ListResponse


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "storage, prefix, limit, continuation_token, expected",
    [
        # Базовый кейс: фильтрация по prefix
        (
            {
                "ns": [
                    "foo/a.txt",
                    "foo/b.txt",
                    "bar/c.txt",
                ],
            },
            "foo/",
            1000,
            OMIT,
            ListResponse(
                storage_paths=["foo/a.txt", "foo/b.txt"],
                continuation_token=None,
            ),
        ),
        # Ограничение limit
        (
            {
                "ns": [
                    "foo/a.txt",
                    "foo/b.txt",
                    "foo/c.txt",
                ],
            },
            "foo/",
            2,
            OMIT,
            ListResponse(
                storage_paths=["foo/a.txt", "foo/b.txt"],
                continuation_token="foo/c.txt",
            ),
        ),
        # continuation_token пропускает предыдущие элементы
        (
            {
                "ns": [
                    "foo/a.txt",
                    "foo/b.txt",
                    "foo/c.txt",
                ],
            },
            "foo/",
            1000,
            "foo/a.txt",
            ListResponse(
                storage_paths=["foo/b.txt", "foo/c.txt"],
                continuation_token=None,
            ),
        ),
        # continuation_token + limit
        (
            {
                "ns": [
                    "foo/a.txt",
                    "foo/b.txt",
                    "foo/c.txt",
                    "foo/d.txt",
                ],
            },
            "foo/",
            2,
            "foo/a.txt",
            ListResponse(
                storage_paths=["foo/b.txt", "foo/c.txt"],
                continuation_token="foo/d.txt",
            ),
        ),
        # Нет совпадений по prefix
        (
            {
                "ns": [
                    "bar/a.txt",
                    "bar/b.txt",
                ],
            },
            "foo/",
            1000,
            OMIT,
            ListResponse(
                storage_paths=[],
                continuation_token=None,
            ),
        ),
        # Пустое хранилище
        (
            {
                "ns": [],
            },
            "foo/",
            1000,
            OMIT,
            ListResponse(
                storage_paths=[],
                continuation_token=None,
            ),
        ),
        # continuation_token указывает после всех элементов
        (
            {
                "ns": [
                    "foo/a.txt",
                    "foo/b.txt",
                ],
            },
            "foo/",
            1000,
            "zzz.txt",
            ListResponse(
                storage_paths=[],
                continuation_token=None,
            ),
        ),
    ],
)
async def test_list_objects(
    storage,
    prefix,
    limit,
    continuation_token,
    expected,
    uow_cls,
    monkeypatch,
):

    async with uow_cls() as uow:
        monkeypatch.setattr(uow.connector.__class__, "_storage", storage)

        result = await uow.connector.list_objects(
            prefix=prefix,
            repo_extra={"namespace": "ns"},
            limit=limit,
            continuation_token=continuation_token,
        )

    assert result == expected


@pytest.mark.asyncio
async def test_list_objects_sorts_storage_before_listing(
    uow_cls,
    monkeypatch,
):

    async with uow_cls() as uow:
        storage = {
            "ns": [
                "foo/c.txt",
                "foo/a.txt",
                "foo/b.txt",
            ],
        }
        monkeypatch.setattr(uow.connector.__class__, "_storage", storage)

        result = await uow.connector.list_objects(
            prefix="foo/",
            repo_extra={"namespace": "ns"},
        )

    assert result.storage_paths == [
        "foo/a.txt",
        "foo/b.txt",
        "foo/c.txt",
    ]


@pytest.mark.asyncio
async def test_list_objects_with_zero_limit(
    uow_cls,
    monkeypatch,
):
    async with uow_cls() as uow:
        storage = {
            "ns": [
                "foo/a.txt",
                "foo/b.txt",
            ],
        }
        monkeypatch.setattr(uow.connector.__class__, "_storage", storage)

        result = await uow.connector.list_objects(
            prefix="foo/",
            repo_extra={"namespace": "ns"},
            limit=0,
        )

    assert result.storage_paths == []
    assert result.continuation_token == "foo/a.txt"
