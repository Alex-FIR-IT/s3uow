from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

    from fennflow._operations.dto import OperationRecord


@dataclass(slots=True)
class OperationPage:
    """Response returned for pagination by backends.

    Attributes:
        operations: Operations of the listed files.
        continuation_token: Opaque token to pass to the next :meth:`ListRepository.list`
            call to retrieve the next page. ``None`` if no more results are available.

    """

    operations: tuple[OperationRecord, ...]
    continuation_token: str | None = None

    def __iter__(self) -> Iterator[OperationRecord]:
        return iter(self.operations)

    def __getitem__(self, item) -> OperationRecord:
        return self.operations[item]

    def __len__(self) -> int:
        return len(self.operations)
