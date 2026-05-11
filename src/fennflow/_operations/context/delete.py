from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from fennflow._operations.context.abstract import BaseContext

if TYPE_CHECKING:
    from fennflow._new_types import Filepath, Namespace


@dataclass(slots=True)
class DeleteContext(BaseContext):
    to_storage_path: Filepath
    to_namespace: Namespace
