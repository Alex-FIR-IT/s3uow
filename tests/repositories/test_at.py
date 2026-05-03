import pytest


@pytest.mark.asyncio
async def test_chain_at(uow_cls, text_files):
    async with uow_cls() as uow:
        storage = uow.user_files.at("user/")
        assert storage.pwd == "user"
        storage = storage.at("shelf1/")
        assert storage.pwd == "user/shelf1"
        storage = storage.at("/")
        assert storage.pwd == "user/shelf1"


@pytest.mark.asyncio
async def test_many_slashes_at(uow_cls, text_files):
    async with uow_cls() as uow:
        storage = uow.user_files.at("user//////")
        assert storage.pwd == "user"


@pytest.mark.asyncio
async def test_root_folder_at(uow_cls, text_files):
    async with uow_cls() as uow:
        storage = uow.user_files.at("/")
        assert storage.pwd == ""
        storage = storage.at("/user1/")
        assert storage.pwd == "user1"


@pytest.mark.asyncio
async def test_empty_path(uow_cls):
    async with uow_cls() as uow:
        storage = uow.user_files.at("")
        assert storage.pwd == ""


@pytest.mark.asyncio
async def test_complex_path_normalization(uow_cls):
    async with uow_cls() as uow:
        storage = uow.user_files.at("///user///shelf1///")
        assert storage.pwd == "user/shelf1"


@pytest.mark.asyncio
async def test_chained_normalization(uow_cls):
    async with uow_cls() as uow:
        storage = uow.user_files.at("///user///")
        storage = storage.at("///shelf1///")
        assert storage.pwd == "user/shelf1"


@pytest.mark.asyncio
async def test_storages_isolation(uow_cls):
    async with uow_cls() as uow:
        storage1 = uow.user_files.at("user/")
        storage2 = uow.user_files.at("admin/")
        assert storage1.pwd == "user"
        assert storage2.pwd == "admin"


@pytest.mark.asyncio
async def test_default_pwd(uow_cls):
    async with uow_cls() as uow:
        assert uow.user_files.pwd == ""
