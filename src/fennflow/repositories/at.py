from typing import Self

from fennflow._path import Path

from .base import BaseRepository


class AtRepository(BaseRepository):
    def _join_path(self, *paths: str) -> str:
        return Path.join_path(self._path, *paths)

    def at(self, path: str) -> Self:
        new_path = self._join_path(path)

        return self.__class__(self._uow, new_path, repo_extra=self.repo_extra)

    @property
    def pwd(self) -> str:
        return Path.normalize_path(self._path)
