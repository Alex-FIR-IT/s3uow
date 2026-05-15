# import pytest
#
# from fennflow.backends.exceptions import RecordLockedException
# from fennflow.files import TextContent
#
#
# def file(name: str) -> TextContent:
#     return TextContent.from_content(f"content of {name}", filename=name)
#
#
# # ---------------------------------------------------------------------------
# # 1. PENDING path blocks another session's CreateRepository
# # ---------------------------------------------------------------------------
#
#
# @pytest.mark.asyncio
# async def test_create_raises_lock_exception_when_path_is_pending(uow_cls):
#     """Session A holds a PENDING create. Session B must get RecordLockedException."""
#     async with uow_cls(auto_commit=False) as uow_a:
#         await uow_a.user_files.at("folder/").create(file("shared.txt"))
#
#         with pytest.raises(RecordLockedException):
#             async with uow_cls() as uow_b:
#                 await uow_b.user_files.at("folder/").create(file("shared.txt"))
#
#         await uow_a.rollback()
#
#
# # ---------------------------------------------------------------------------
# # 2. PENDING path blocks another session's PutRepository (overwrite)
# # ---------------------------------------------------------------------------
#
#
# @pytest.mark.asyncio
# async def test_put_raises_lock_exception_when_path_is_pending(uow_cls):
#     """Session A holds a PENDING create. Session B overwrite must get RecordLockedException."""
#     async with uow_cls(auto_commit=False) as uow_a:
#         await uow_a.user_files.at("folder/").create(file("shared.txt"))
#
#         with pytest.raises(RecordLockedException):
#             async with uow_cls() as uow_b:
#                 await uow_b.user_files.at("folder/").put(file("shared.txt"))
#
#         await uow_a.rollback()
#
#
# # ---------------------------------------------------------------------------
# # 3. Lock releases after commit
# # ---------------------------------------------------------------------------
#
#
# @pytest.mark.asyncio
# async def test_lock_releases_after_commit(uow_cls):
#     """After session A commits, session B can overwrite the same path."""
#     async with uow_cls() as uow_a:
#         await uow_a.user_files.at("folder/").create(file("shared.txt"))
#
#     async with uow_cls() as uow_b:
#         await uow_b.user_files.at("folder/").put(file("shared.txt"))
#
#
# # ---------------------------------------------------------------------------
# # 4. Lock releases after rollback
# # ---------------------------------------------------------------------------
#
#
# @pytest.mark.asyncio
# async def test_lock_releases_after_rollback(uow_cls):
#     """After session A rolls back, session B can create the same path."""
#     async with uow_cls(auto_commit=False) as uow_a:
#         await uow_a.user_files.at("folder/").create(file("shared.txt"))
#         await uow_a.rollback()
#
#     async with uow_cls() as uow_b:
#         await uow_b.user_files.at("folder/").create(file("shared.txt"))
#
#
# # ---------------------------------------------------------------------------
# # 5. Different paths do not interfere
# # ---------------------------------------------------------------------------
#
#
# @pytest.mark.asyncio
# async def test_different_paths_do_not_interfere(uow_cls):
#     """Session A locks path X. Session B writes path Y. No RecordLockedException."""
#     async with uow_cls(auto_commit=False) as uow_a:
#         await uow_a.user_files.at("folder/").create(file("x.txt"))
#
#         async with uow_cls() as uow_b:
#             await uow_b.user_files.at("folder/").create(file("y.txt"))
#
#         await uow_a.rollback()
