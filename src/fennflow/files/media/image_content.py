from typing import Literal

from .binary_content import BinaryContent


class ImageContent(BinaryContent):
    """Media content representing an image file.

    Attributes:
        height: Height of the image in pixels, if known.
        width: Width of the image in pixels, if known.
    """

    kind: Literal["image"] = "image"

    height: int | None = None
    width: int | None = None
