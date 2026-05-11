from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

    from fennflow._new_types import Filepath


@dataclass(slots=True)
class ListResponse:
    """Response returned by :meth:`ListRepository.list`.

    Attributes:
        storage_paths: storage_paths of the listed files.
        continuation_token: Opaque token to pass to the next :meth:`ListRepository.list`
            call to retrieve the next page. ``None`` if no more results are available.

    Example::

        page = await uow.files.at("folder1/").list(limit=2)
        for storage_path in page:
            print(storage_path)
        if page.continuation_token:
            next_page = await uow.files.at("folder1/").list(
                limit=2,
                continuation_token=page.continuation_token,
            )
    """

    storage_paths: list[Filepath] | tuple[Filepath, ...] = field(default_factory=tuple)
    continuation_token: str | None = None

    def __iter__(self) -> Iterator[Filepath]:
        return iter(self.storage_paths)

    def __getitem__(self, item) -> Filepath:
        return self.storage_paths[item]

    def __len__(self) -> int:
        return len(self.storage_paths)
