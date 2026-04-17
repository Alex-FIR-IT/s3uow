from typing import Literal

from .binary_content import BinaryContent


class AudioContent(BinaryContent):
    kind: Literal["audio"] = "audio"

    duration: int | None = None
