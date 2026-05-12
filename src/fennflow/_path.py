from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fennflow._new_types import StoragePath


class Path:
    @staticmethod
    def normalize_path(path: str) -> StoragePath:
        path = re.sub(r"/+", "/", path)
        return path.strip("/")

    @classmethod
    def join_path(cls, *paths: str) -> StoragePath:
        path = "/".join(path for path in paths)

        return cls.normalize_path(path)

    @classmethod
    def normalize_folder(cls, path: str) -> str:
        """Used for display of folder path.

        Adds trailing slash to distinguish folders from file keys.
        _path itself has no trailing slash as it's used directly in join operations.

        """
        normalized = cls.normalize_path(path)
        return normalized + "/" if normalized else ""
