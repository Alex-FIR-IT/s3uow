from __future__ import annotations

from typing import TYPE_CHECKING

from fennflow._path import Path

if TYPE_CHECKING:
    from fennflow._new_types import StoragePath
    from fennflow._operations.dto import OperationRecord


class TmpPathBuilder:
    @staticmethod
    def from_operation(operation: OperationRecord) -> StoragePath:
        return Path.join_path(
            "tmp",
            f"session_id_{operation.session_id}",
            f"operation_id_{operation.session_id}",
            operation.storage_path,
        )
