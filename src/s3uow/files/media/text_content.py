from typing import Literal, Self

from .abstract.content import ContentPropertyAbstract
from .abstract.from_content import FromContentAbstract
from .binary_content import BinaryContent


class TextContent(BinaryContent, FromContentAbstract, ContentPropertyAbstract,):
    kind: Literal["txt"] = "txt"
    encoding: str = "utf-8"

    @property
    def content(self) -> str:
        try:
            return self.data.decode(self.encoding)
        except UnicodeDecodeError as e:
            raise ValueError(f"Cannot extract text from {self=}")


    @classmethod
    def from_content(
        cls,
        data: str,
        encoding: str = "utf-8",
        media_type: str = "text/plain",
    ) -> Self:
        return cls(
            data=data.encode(encoding),
            media_type=media_type,
            encoding=encoding,
        )
