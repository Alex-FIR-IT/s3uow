from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterator

if TYPE_CHECKING:
    from fennflow._operations.dto import OperationRecord


@dataclass(slots=True)
class OperationPage:
    operations: tuple[OperationRecord, ...]
    continuation_token: str | None = None
    
    def __iter__(self) -> Iterator[OperationRecord]:
        return iter(self.operations)

    def __getitem__(self, item) -> OperationRecord:
        return self.operations[item]

    def __len__(self) -> int:
        return len(self.operations)


