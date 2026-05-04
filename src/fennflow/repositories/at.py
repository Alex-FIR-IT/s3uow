from typing import Self

from fennflow._path import Path

from .base import BaseRepository


class AtRepository(BaseRepository):
    """Repository mixin that adds path navigation capabilities.

    Allows scoping operations to a specific path within the namespace
    using the ``at()`` method.

    Example:
        await uow.user_files.at("user1/").put(file)
    """

    def _join_path(self, *paths: str) -> str:
        """Join the current path with one or more path segments.

        Args:
            *paths: Path segments to append to the current path.

        Returns:
            The joined and normalized path string.
        """
        return Path.join_path(self._path, *paths)

    def at(self, path: str) -> Self:
        """Return a new repository instance scoped to the given path.

        Args:
            path: Path to scope the repository to, relative to the current path.

        Returns:
            A new repository instance with the updated path.

        Example:
            storage = uow.user_files.at("user1/")
            await storage.put(file)
        """
        new_path = self._join_path(path)

        return self.__class__(self._uow, new_path, repo_extra=self.repo_extra)

    @property
    def pwd(self) -> str:
        """Return the current working path.

        Returns:
            The normalized current path string.
        """
        return Path.normalize_path(self._path)
