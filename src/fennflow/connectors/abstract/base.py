from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from fennflow._sentinel import OMIT, Omittable
from fennflow.repositories.fields.base import RepoExtra

if TYPE_CHECKING:
    from typing_extensions import Self

    from fennflow._new_types import Namespace, StoragePath
    from fennflow.files.responses.base import MediaResponse
    from fennflow.files.responses.list import ListResponse
    from fennflow.files.types import BinaryMedia

RepoExtraType = TypeVar("RepoExtraType", bound=RepoExtra)


class AbstractConnector(ABC, Generic[RepoExtraType]):
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
        repo_extra: RepoExtraType,
        **extra: dict[Any, Any],
    ) -> Any:
        """Upload a file to storage."""

    @abstractmethod
    async def get(
        self,
        storage_path: StoragePath,
        repo_extra: RepoExtraType,
        **extra: dict[Any, Any],
    ) -> MediaResponse:
        """Download a file from storage."""

    @abstractmethod
    async def delete(
        self,
        storage_path: StoragePath,
        repo_extra: RepoExtraType,
        **extra: dict[Any, Any],
    ):
        """Delete a file from storage."""

    @abstractmethod
    async def copy_object(
        self,
        repo_extra: RepoExtraType,
        from_storage_path: StoragePath,
        to_storage_path: StoragePath,
        to_namespace: Namespace,
        **extra: dict[Any, Any],
    ):
        """Copy a file within or across namespaces."""

    @abstractmethod
    async def list_objects(
        self,
        prefix: str,
        repo_extra: RepoExtraType,
        limit: int = 1000,
        continuation_token: Omittable[str] | None = OMIT,
        **extra: dict[Any, Any],
    ) -> ListResponse:
        """List all files in storage."""
