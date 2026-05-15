from copy import deepcopy

import pytest

from fennflow.files import TextContent
from fennflow.repositories.exceptions import FilepathsCollisionError


@pytest.mark.asyncio
async def test_simple_put(uow_cls, text_files):
    async with uow_cls() as uow:
        await uow.user_files.at("user/").put(text_files[0])

        response = await uow.user_files.at("user/").get(text_files[0].filename)
        print("TYPES:", type(response[0]), type(text_files[0]))
        print("DIFFERENCE:", response[0].model_dump() == text_files[0].model_dump())
        assert response[0].data == text_files[0].data


@pytest.mark.asyncio
async def test_upsert(uow_cls, text_files):
    async with uow_cls() as uow:
        await uow.user_files.at("user/").put(text_files[0])

        another_file = deepcopy(text_files[0])
        another_file.data = b"another_file_data"
        await uow.user_files.at("user/").put(another_file)

        response = await uow.user_files.at("user/").get(another_file.filename)
        response2 = await uow.user_files.at("user/").get(text_files[0].filename)

        assert response[0].data != text_files[0].data
        assert response[0].data == another_file.data
        assert response == response2


@pytest.mark.asyncio
async def test_upsert_last_file_is_saved(uow_cls):
    async with uow_cls() as uow:
        files = []
        filename = "text.txt"
        for index in range(100):
            files.append(
                TextContent.from_content(
                    f"{index}",
                    filename=filename,
                )
            )
        for file in files:
            await uow.user_files.at("user/").put(file)

        response = await uow.user_files.at("user/").get(filename)

        assert response[0].data == files[-1].data


@pytest.mark.asyncio
async def test_upsert_rollback_returned_original_file(uow_cls):
    async with uow_cls() as uow:
        files = []
        filename = "text.txt"
        for index in range(100):
            files.append(
                TextContent.from_content(
                    f"{index}",
                    filename=filename,
                )
            )
        original_file = TextContent.from_content(
            data="orignal_file_data",
            filename=filename,
        )
        await uow.user_files.at("user/").put(original_file)
        await uow.commit()

        for file in files:
            await uow.user_files.at("user/").put(file)

        response = await uow.user_files.at("user/").get(filename)
        assert response[0].data == files[-1].data
        assert response[0].data != original_file.data

        await uow.rollback()

        response = await uow.user_files.at("user/").get(filename)
        assert response[0].data != files[-1].data
        assert response[0].data == original_file.data


@pytest.mark.asyncio
async def test_put_multiply_files_with_same_name_raises(uow_cls):
    async with uow_cls() as uow:
        files = []
        filename = "text.txt"
        for index in range(100):
            files.append(
                TextContent.from_content(
                    f"{index}",
                    filename=filename,
                )
            )
        with pytest.raises(FilepathsCollisionError):
            await uow.user_files.at("user/").put(*files)

        response = await uow.user_files.at("user/").get(filename)

        assert len(response) == 0
