from collections.abc import Iterator
from dataclasses import dataclass

from pydantic import Field

from fennflow._new_types import Filepath


@dataclass(slots=True)
class ListResponse:
    """Response returned by :meth:`ListRepository.list`.

    Attributes:
        filepaths: Filepaths of the listed files.
        continuation_token: Opaque token to pass to the next :meth:`ListRepository.list`
            call to retrieve the next page. ``None`` if no more results are available.

    Example::

        page = await uow.files.at("folder1/").list(limit=2)
        for filepath in page:
            print(filepath)
        if page.continuation_token:
            next_page = await uow.files.at("folder1/").list(
                limit=2,
                continuation_token=page.continuation_token,
            )
    """

    filepaths: tuple[Filepath, ...] = Field(default_factory=tuple)
    continuation_token: str | None = None

    def __iter__(self) -> Iterator[Filepath]:
        return iter(self.filepaths)

    def __getitem__(self, item) -> Filepath:
        return self.filepaths[item]

    def __len__(self) -> int:
        return len(self.filepaths)
