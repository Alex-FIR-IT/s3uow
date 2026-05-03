from __future__ import annotations

from typing import Generic, TypeVar

from typing_extensions import overload

RepoType = TypeVar("RepoType")


class RepoField(Generic[RepoType]):
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
