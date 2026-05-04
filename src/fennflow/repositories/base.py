from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import TypedDict

if TYPE_CHECKING:
    from fennflow.uow.base import UnitOfWork


class RepoExtra(TypedDict):
    """Base configuration passed to every repository instance.

    Attributes:
        namespace: The storage namespace (e.g. S3 bucket name).
    """

    namespace: str


class BaseRepository:  # noqa: B903
    """Base class for all FennFlow repositories.

    Provides access to the UnitOfWork, current path, and connector configuration.
    Not meant to be used directly — use mixins like PutRepository, GetRepository etc.

    Args:
        uow: The UnitOfWork instance managing this repository's session.
        path: The current working path within the namespace.
        repo_extra: Connector-specific configuration including namespace.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        path: str,
        repo_extra: RepoExtra,
    ):
        self._uow = uow
        self._path = path
        self.repo_extra = repo_extra
