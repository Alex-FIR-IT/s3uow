from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable
    from uuid import UUID

    from fennflow._new_types import Filepath
    from fennflow._operations.dto import OperationRecord
    from fennflow.backends.abstract.config import AbstractBackendConfig
    from fennflow.backends.enums import OnConflictDoEnum
    from fennflow.backends.responses import OperationPage


class AbstractBackend(ABC):
    """Base class for all backends."""

    def __init__(self, config: AbstractBackendConfig) -> None:
        self._config = config
        self._operations: dict[Filepath, OperationRecord] = {}

    @abstractmethod
    async def open(self) -> None: ...

    @abstractmethod
    async def close(self) -> None: ...

    @abstractmethod
    async def get(
        self,
        storage_path: Filepath,
    ) -> OperationRecord | None: ...

    @abstractmethod
    async def add(self, record: OperationRecord) -> None: ...

    @abstractmethod
    async def exists(
        self,
        storage_path: Filepath,
    ) -> bool: ...

    @abstractmethod
    async def list_pending(
        self,
    ) -> list[OperationRecord]: ...

    @abstractmethod
    async def mark_done(self, operation: OperationRecord) -> None: ...

    @abstractmethod
    async def mark_failed(
        self,
        operation: OperationRecord,
        error: str | None = None,
    ): ...

    @abstractmethod
    async def mark_compensation_failed(
        self,
        operation: OperationRecord,
        error: str | None = None,
    ): ...

    @abstractmethod
    async def clear_session(self) -> None: ...

    @abstractmethod
    async def flush(self): ...

    @abstractmethod
    async def rollback(self): ...

    @abstractmethod
    async def get_visible(
        self,
        prefix: str,
        continuation_token: str,
        limit: int,
        session_id: UUID,
    ) -> OperationPage: ...

    @abstractmethod
    async def insert(
        self,
        operations: Iterable[OperationRecord],
        on_conflict: OnConflictDoEnum,
    ) -> None: ...

    @abstractmethod
    async def is_empty(self) -> bool: ...
