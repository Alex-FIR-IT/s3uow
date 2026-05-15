from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from fennflow._operations.context.abstract import BaseContext

if TYPE_CHECKING:
    from fennflow.files.types import BinaryMedia


@dataclass(slots=True)
class CreateContext(BaseContext):
    file: BinaryMedia
