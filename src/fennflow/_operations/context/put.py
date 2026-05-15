from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from fennflow._operations.context.abstract import BaseContext
from fennflow._sentinel import NOT_GIVEN, NotGiven

if TYPE_CHECKING:
    from fennflow._new_types import StoragePath
    from fennflow.files.types import BinaryMedia


@dataclass(slots=True)
class PutContext(BaseContext):
    file: BinaryMedia
    tmp_path: StoragePath | NotGiven = NOT_GIVEN
