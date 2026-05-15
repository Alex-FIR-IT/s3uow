from collections.abc import Collection, Sequence
from typing import Any

from fennflow.files.types import BinaryMedia
from fennflow.repositories.exceptions import FilepathsCollisionError


class ValidateDuplicatesMixin:
    @staticmethod
    def validate_duplicates(objs: Collection[Any]) -> None:
        if len(objs) != len(set(objs)):
            raise FilepathsCollisionError()

    @classmethod
    def validate_duplicates_from_files(
        cls,
        files: Sequence[BinaryMedia],
    ) -> None:
        filenames = tuple(file.filename for file in files)

        return cls.validate_duplicates(filenames)
