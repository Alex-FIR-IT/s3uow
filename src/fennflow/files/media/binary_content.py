import base64
from typing import Any

from pydantic import (
    Field,
    computed_field,
    field_serializer,
    field_validator,
)

from fennflow.files.media.base import BaseContent


class BinaryContent(BaseContent):
    """Base class for binary content type."""

    data: bytes = Field(repr=False)
    kind: str = "binary"

    @field_serializer("*", mode="wrap")
    def serialize_numbers(self, value: Any, handler: Any) -> Any:
        result = handler(value)
        if isinstance(result, (int, float)) and not isinstance(result, bool):
            return str(result)
        if result is None:
            return "None"
        return result

    @computed_field
    @property
    def data_size_mb(self) -> float:
        size_bytes = len(self.data)
        size_mb = round(size_bytes / (1024 * 1024), 2)
        return size_mb

    @field_serializer("data")
    def ser_data(self, v: bytes, _info):
        return base64.b64encode(v).decode("ascii")

    @field_validator("data", mode="before")
    @classmethod
    def de_data(cls, v):
        if isinstance(v, str):
            return base64.b64decode(v)
        return v
