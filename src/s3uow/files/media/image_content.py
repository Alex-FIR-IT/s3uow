from typing import Literal

from .binary_content import BinaryContent


class ImageContent(BinaryContent):
    kind: Literal["image"] = "image"

    height: int | None = None
    width: int | None = None
