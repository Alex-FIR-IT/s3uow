from typing import Literal, Self
import json
from pydantic import JsonValue

from .abstract.content import ContentPropertyAbstract
from .abstract.from_content import FromContentAbstract
from .binary_content import BinaryContent


class JsonContent[Value: JsonValue](
    BinaryContent,
    FromContentAbstract,
    ContentPropertyAbstract,
):
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
        media_type: str = "text/plain",
        ensure_ascii: bool = False,
        indent: int = 4,
    ) -> Self:
        dumped_data = json.dumps(data, ensure_ascii=ensure_ascii, indent=indent)
        return cls(
            data=dumped_data.encode(encoding),
            media_type=media_type,
            encoding=encoding,
        )
