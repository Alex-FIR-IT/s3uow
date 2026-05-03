from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from fennflow._new_types import Filepath, Namespace
    from fennflow.files.responses.base import MediaResponse
    from fennflow.files.types import BinaryMedia


class AbstractConnector(ABC):
    @abstractmethod
    async def open(self) -> Self: ...

    @abstractmethod
    async def close(self) -> Any: ...

    @abstractmethod
    async def put(
        self,
        file: BinaryMedia,
        repo_extra: dict[Any, Any],
        **extra: dict[Any, Any],
    ) -> Any: ...

    @abstractmethod
    async def get(
        self,
        filepath: Filepath,
        repo_extra: dict[Any, Any],
        **extra: dict[Any, Any],
    ) -> MediaResponse: ...

    @abstractmethod
    async def delete(
        self,
        filepath: Filepath,
        repo_extra: dict[Any, Any],
        **extra: dict[Any, Any],
    ): ...

    @abstractmethod
    async def copy_object(
        self,
        repo_extra: dict[Any, Any],
        from_filepath: Filepath,
        to_filepath: Filepath,
        to_namespace: Namespace,
        **extra: dict[Any, Any],
    ): ...
