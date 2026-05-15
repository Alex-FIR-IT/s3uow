from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from typing_extensions import Unpack

from fennflow._operations.context.abstract import BaseContext
from fennflow._operations.enums import OperationStatusEnum, OperationTypeEnum
from fennflow._sentinel import OMIT, Omittable
from fennflow.backends.abstract.base import AbstractBackend
from fennflow.backends.enums import OnConflictDoEnum
from fennflow.backends.exceptions import RecordAlreadyExistsException
from fennflow.backends.in_memory._select import SelectOperation

if TYPE_CHECKING:
    from collections.abc import Iterable
    from uuid import UUID

    from fennflow._new_types import BackendScope, StoragePath
    from fennflow._operations.dto import OperationRecord
    from fennflow.backends.abstract.annotations import SelectParams
    from fennflow.backends.in_memory import InMemoryBackendConfig
    from fennflow.backends.responses import OperationPage


class InMemoryBackend(AbstractBackend):
    """In-memory backend for managing file operations within a Unit of Work."""

    _storage: defaultdict[BackendScope, dict[StoragePath, OperationRecord]] | None = (
        None
    )

    def __init__(
        self,
        config: InMemoryBackendConfig,
    ):
        super().__init__(config=config)
        if self.__class__._storage is None:
            self.__class__._storage = defaultdict(dict)

    @property
    def storage(
        self,
    ) -> defaultdict[BackendScope, dict[StoragePath, OperationRecord]]:
        if self.__class__._storage is None:
            raise RuntimeError(
                "Cannot get in-memory storage. InMemoryBackend is not initialized.",
            )
        return self.__class__._storage

    @property
    def scoped_storage(self) -> dict[StoragePath, OperationRecord]:
        return self.storage[self._config.scope]

    async def open(
        self,
    ) -> None:
        pass

    async def close(
        self,
    ) -> None:
        await self.clear_session()

    async def add(
        self,
        record: OperationRecord,
        on_conflict: OnConflictDoEnum = OnConflictDoEnum.RAISE,
    ) -> None:
        existing_record = self._operations.get(record.storage_path)

        if existing_record is not None:
            if on_conflict == OnConflictDoEnum.RAISE:
                raise RecordAlreadyExistsException()
            elif on_conflict == OnConflictDoEnum.DO_NOTHING:
                return
            elif on_conflict == OnConflictDoEnum.REPLACE:
                self._operations[record.storage_path] = record
            else:
                raise AssertionError("Unhandled conflict strategy.")

        self._operations[record.storage_path] = record

    async def exists(
        self,
        storage_path: StoragePath,
    ) -> bool:
        return storage_path in self.storage[self._config.scope]

    async def get_from_backend(
        self,
        storage_path: StoragePath,
    ) -> OperationRecord | None:
        return self.storage[self._config.scope].get(storage_path)

    async def get(
        self,
        storage_path: StoragePath,
    ) -> OperationRecord | None:
        return self._operations.get(storage_path) or self.storage[
            self._config.scope
        ].get(storage_path)

    async def list_pending(
        self,
    ) -> list[OperationRecord]:
        return [
            operation for operation in self._operations.values() if operation.is_pending
        ]

    async def mark_done(
        self,
        operation: OperationRecord,
    ) -> None:
        if operation.operation_type in {
            OperationTypeEnum.CREATE,
            OperationTypeEnum.PUT,
        }:
            operation.status = OperationStatusEnum.UPLOADED
        elif operation.operation_type == OperationTypeEnum.DELETE:
            operation.status = OperationStatusEnum.DELETED
        else:
            raise NotImplementedError(
                f"mark_done is not supported for {operation.operation_type=}"
            )

    async def mark_failed(
        self,
        operation: OperationRecord,
        error: str | None = None,
    ) -> None:
        operation.status = OperationStatusEnum.FAILED
        operation.error = error

    async def mark_compensation_failed(
        self,
        operation: OperationRecord,
        error: str | None = None,
    ):
        operation.status = OperationStatusEnum.COMPENSATION_FAILED
        operation.error = error

    async def mark_pending(
        self,
        operation: OperationRecord,
    ) -> None:
        operation.status = OperationStatusEnum.PENDING

    async def clear_session(
        self,
    ) -> None:
        for op in self._operations.values():
            op.context = BaseContext()

        self._operations.clear()

    async def flush(
        self,
    ):
        for key, operation in self._operations.items():
            storage_operation = await self.get_from_backend(
                storage_path=operation.storage_path,
            )

            if storage_operation and storage_operation.is_locked(
                current_session_id=operation.session_id
            ):
                raise RecordAlreadyExistsException(
                    f"{operation.storage_path=} already exists"
                )
            self.storage[self._config.scope][key] = operation

    async def rollback(
        self,
        error: str | None = None,
    ) -> None:
        for operation in self._operations.values():
            await self.mark_failed(
                operation=operation,
                error=error,
            )

    @classmethod
    def drop_all(cls) -> None:
        cls._storage = defaultdict(dict)

    async def select(
        self,
        **kwargs: Unpack[SelectParams],
    ) -> OperationPage:
        select = SelectOperation(**kwargs)

        return select.select(record=(record for record in self.scoped_storage.values()))

    async def get_visible(
        self,
        prefix: str,
        limit: int,
        session_id: UUID,
        continuation_token: Omittable[str] = OMIT,
    ) -> OperationPage:
        return await self.select(
            prefix=prefix,
            continuation_token=continuation_token,
            limit=limit,
            visible_for_session_id=session_id,
        )

    async def is_empty(self) -> bool:
        return not bool(self.scoped_storage)

    async def insert(
        self,
        operations: Iterable[OperationRecord],
        on_conflict: OnConflictDoEnum,
    ) -> None:
        for operation in operations:
            op_in_storage = self.scoped_storage.get(operation.storage_path)

            if op_in_storage:
                match on_conflict:
                    case OnConflictDoEnum.DO_NOTHING:
                        continue
                    case OnConflictDoEnum.REPLACE:
                        self.scoped_storage[operation.storage_path] = operation
                    case OnConflictDoEnum.RAISE:
                        raise ValueError(
                            f"There is already record with {operation.storage_path=}"
                        )
                    case _:
                        raise AssertionError("Unhandled conflict strategy.")
            else:
                self.scoped_storage[operation.storage_path] = operation
