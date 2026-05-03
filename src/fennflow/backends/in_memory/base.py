from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from fennflow.backends.abstract.base import AbstractBackend
from fennflow.backends.abstract.exceptions import RecordAlreadyExistsException

if TYPE_CHECKING:
    from fennflow._new_types import Filepath, Namespace
    from fennflow._operations.dto import OperationRecord
    from fennflow.backends.in_memory import InMemoryBackendConfig


class InMemoryBackend(AbstractBackend):
    """In-memory backend for managing file operations within a Unit of Work."""

    _storage: defaultdict[Namespace, dict[Filepath, OperationRecord]] | None = None

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
    ) -> defaultdict[Namespace, dict[Filepath, OperationRecord]]:
        if self.__class__._storage is None:
            raise RuntimeError(
                "Cannot get in-memory storage. InMemoryBackend is not initialized.",
            )
        return self.__class__._storage

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
    ) -> None:
        self._operations[record.filepath] = record

    async def exists(
        self,
        filepath: str,
        namespace: Namespace,
    ) -> bool:
        return filepath in self.storage[namespace]

    async def get_from_storage(
        self,
        filepath: str,
        namespace: str,
    ) -> OperationRecord | None:
        return self.storage[namespace].get(filepath)

    async def get(
        self,
        filepath: str,
        namespace: str,
    ) -> OperationRecord | None:
        return self._operations.get(filepath) or self.storage[namespace].get(filepath)

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
        operation.status = "uploaded"

    async def mark_failed(
        self,
        operation: OperationRecord,
        error: str | None = None,
    ) -> None:
        operation.status = "failed"
        operation.error = error

    async def mark_compensation_failed(
        self,
        operation: OperationRecord,
        error: str | None = None,
    ):
        operation.status = "compensation_failed"
        operation.error = error

    async def mark_pending(
        self,
        operation: OperationRecord,
    ) -> None:
        operation.status = "pending"

    async def clear_session(
        self,
    ) -> None:
        self._operations.clear()

    async def flush(
        self,
    ):
        for key, operation in self._operations.items():
            storage_operation = await self.get_from_storage(
                filepath=operation.filepath,
                namespace=operation.namespace,
            )

            if storage_operation and storage_operation.is_locked(
                current_session_id=operation.session_id
            ):
                raise RecordAlreadyExistsException(
                    f"{operation.filepath=} already exists"
                )
            self.storage[operation.namespace][key] = operation

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
