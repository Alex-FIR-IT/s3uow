import json
from typing import Generic, Literal, Self, TypeVar

from pydantic import JsonValue

from .abstract.content import ContentPropertyAbstract
from .abstract.from_content import FromContentAbstract
from .binary_content import BinaryContent

Value = TypeVar("Value", bound=JsonValue)


class JsonContent(
    BinaryContent,
    FromContentAbstract,
    ContentPropertyAbstract,
    Generic[Value],
):
    """Media content representing a JSON file.

    Stores JSON data as UTF-8 encoded bytes internally.
    Use ``from_content()`` to create from a Python object.

    Attributes:
        encoding: The text encoding. Defaults to ``"utf-8"``.

    Example::

        file = JsonContent.from_content({"key": "value"})
        print(file.content) # {"key": "value"}
        await uow.user_files.at("user1/").put(file)
    """

    kind: Literal["json"] = "json"
    encoding: str = "utf-8"

    @property
    def content(self) -> Value:
        text = self.data.decode(self.encoding)
        return json.loads(text)

    @classmethod
    def from_content(
        cls,
        data: Value,
        encoding: str = "utf-8",
        media_type: str = "application/json",
        ensure_ascii: bool = False,
        indent: int = 4,
    ) -> Self:
        dumped_data = json.dumps(data, ensure_ascii=ensure_ascii, indent=indent)
        return cls(
            data=dumped_data.encode(encoding),
            media_type=media_type,
            encoding=encoding,
        )
