from typing import Literal

from .binary_content import BinaryContent


class VideoContent(BinaryContent):
    kind: Literal["video"] = "video"

    duration: int
    height: int
    width: int
