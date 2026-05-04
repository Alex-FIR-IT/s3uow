from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fennflow._new_types import Filepath


class Path:
    @staticmethod
    def normalize_path(path: str) -> Filepath:
        path = re.sub(r"/+", "/", path)
        return path.strip("/")

    @classmethod
    def join_path(cls, *paths: str) -> Filepath:
        path = "/".join(path.strip("/") for path in paths)

        return cls.normalize_path(path)
