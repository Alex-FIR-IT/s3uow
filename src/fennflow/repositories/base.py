from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import TypedDict

if TYPE_CHECKING:
    from fennflow.uow.base import UnitOfWork


class RepoExtra(TypedDict):
    namespace: str


class BaseRepository:  # noqa: B903
    def __init__(
        self,
        uow: UnitOfWork,
        path: str,
        repo_extra: RepoExtra,
    ):
        self._uow = uow
        self._path = path
        self.repo_extra = repo_extra
