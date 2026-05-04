from typing import Literal, Self

from .abstract.content import ContentPropertyAbstract
from .abstract.from_content import FromContentAbstract
from .binary_content import BinaryContent


class TextContent(
    BinaryContent,
    FromContentAbstract,
    ContentPropertyAbstract,
):
    """Media content representing a plain text file.

    Stores text as UTF-8 encoded bytes internally.
    Use ``from_content()`` to create from a string.

    Attributes:
        encoding: The text encoding. Defaults to ``"utf-8"``.

    Example::

        file = TextContent.from_content("Hello, World!")
        print(file.content) # "Hello, World!"
        await uow.user_files.at("user1/").put(file)
    """

    kind: Literal["txt"] = "txt"
    encoding: str = "utf-8"

    @property
    def content(self) -> str:
        try:
            return self.data.decode(self.encoding)
        except UnicodeDecodeError as e:
            raise ValueError(f"Cannot extract text from {self=}") from e

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
