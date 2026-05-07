from typing import Iterator

from pydantic import BaseModel, Field

from fennflow._new_types import Filepath


class ListResponse(BaseModel):
    filepaths: tuple[Filepath, ...] = Field(default_factory=tuple)
    continuation_token: str | None = None

    def __iter__(self) -> Iterator[Filepath]:
        return iter(self.filepaths)

    def __getitem__(self, item) -> Filepath:
        return self.filepaths[item]

    def __len__(self) -> int:
        return len(self.filepaths)
