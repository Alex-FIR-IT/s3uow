from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypedDict, TypeVar

from typing_extensions import overload

if TYPE_CHECKING:
    from fennflow._new_types import Namespace

RepoType = TypeVar("RepoType")


class RepoExtra(TypedDict):
    """Base configuration passed to every repository instance.

    Attributes:
        namespace: The storage namespace (e.g. S3 bucket name).
    """

    namespace: Namespace


class RepoField(Generic[RepoType]):
    """A descriptor that lazily initializes a repository instance on a UnitOfWork.

    Args:
        repo_cls: The repository class to instantiate.
        namespace: The storage namespace (e.g. S3 bucket name) for this repository.
        **repo_extra: Additional connector-specific configuration
        passed to the repository.

    Example:
        class UOW(UnitOfWork):
            user_files = RepoField(UserFiles, namespace="user-files")

    """

    def __init__(
        self,
        repo_cls: type[RepoType],
        *,
        namespace: str,
        **repo_extra,
    ):
        self.repo_cls = repo_cls
        repo_extra["namespace"] = namespace
        self.repo_extra = repo_extra

    def __set_name__(
        self,
        owner,
        name,
    ):
        self.name = name

    @overload
    def __get__(
        self,
        instance: None,
        owner,
    ) -> RepoField[RepoType]: ...

    @overload
    def __get__(
        self,
        instance,
        owner,
    ) -> RepoType: ...

    def __get__(
        self,
        instance,
        owner,
    ):
        if instance is None:
            return self

        repo = instance.__dict__.get(self.name)
        if repo is None:
            repo = self.repo_cls(
                uow=instance,
                path="/",
                repo_extra=self.repo_extra,
            )
            instance.__dict__[self.name] = repo

        return repo
