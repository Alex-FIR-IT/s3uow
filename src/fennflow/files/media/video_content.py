from typing import Literal

from .binary_content import BinaryContent


class VideoContent(BinaryContent):
    kind: Literal["video"] = "video"

    duration: int | None = None
    height: int | None = None
    width: int | None = None
