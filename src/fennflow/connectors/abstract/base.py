from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from fennflow._new_types import Filepath, Namespace
    from fennflow.files.responses.base import MediaResponse
    from fennflow.files.types import BinaryMedia


class AbstractConnector(ABC):
    """Base class for all FennFlow storage connectors.

    A connector is responsible for performing actual file operations
    against a storage backend (e.g. S3, local filesystem, in-memory).
    All operations are async and integrate with the Saga execution flow
    via ``OperationExecutor``.

    To implement a custom connector, subclass this and implement all
    abstract methods. Register it in ``connector_registry`` to make it
    available via ``ConnectorFactory``.
    """

    @abstractmethod
    async def open(self) -> Self:
        """Initialize the connector and return self."""

    @abstractmethod
    async def close(self) -> Any:
        """Clean up resources."""

    @abstractmethod
    async def put(
        self,
        file: BinaryMedia,
        repo_extra: dict[Any, Any],
        **extra: dict[Any, Any],
    ) -> Any:
        """Upload a file to storage."""

    @abstractmethod
    async def get(
        self,
        filepath: Filepath,
        repo_extra: dict[Any, Any],
        **extra: dict[Any, Any],
    ) -> MediaResponse:
        """Download a file from storage."""

    @abstractmethod
    async def delete(
        self,
        filepath: Filepath,
        repo_extra: dict[Any, Any],
        **extra: dict[Any, Any],
    ):
        """Delete a file from storage."""

    @abstractmethod
    async def copy_object(
        self,
        repo_extra: dict[Any, Any],
        from_filepath: Filepath,
        to_filepath: Filepath,
        to_namespace: Namespace,
        **extra: dict[Any, Any],
    ):
        """Copy a file within or across namespaces."""
