from typing import Self

from ..._sentinel import OMIT, Omittable, is_given
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
        media_type: str = "text/plain",
        encoding: str = "utf-8",
        filename: Omittable[str] = OMIT,
        **kwargs,  # noqa: ARG003
    ) -> Self:
        extra = {}

        if is_given(filename):
            extra["filename"] = filename

        return cls(
            data=data.encode(encoding),
            media_type=media_type,
            encoding=encoding,
            **extra,
        )
