from __future__ import annotations

from fennflow.files.media import (
    AudioContent,
    BinaryContent,
    DocumentContent,
    ImageContent,
    JsonContent,
    TextContent,
    VideoContent,
)

content_registry: dict[str, type[BinaryContent]] = {
    "text/plain": TextContent,
    "text/": TextContent,
    "image/": ImageContent,
    "application/json": JsonContent,
    "audio/": AudioContent,
    "video/": VideoContent,
    "application/pdf": DocumentContent,
}
