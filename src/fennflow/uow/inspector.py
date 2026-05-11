from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from fennflow.repositories import RepoField

if TYPE_CHECKING:
    from collections.abc import Generator

    from fennflow.uow.base import UnitOfWork


@dataclass(slots=True, frozen=True)
class UowInspector:
    """Extracts info from Unit of Work."""

    uow: UnitOfWork

    def get_repo_fields(self) -> Generator[RepoField, None, None]:
        for field in vars(type(self.uow)).values():
            if isinstance(field, RepoField):
                yield field
