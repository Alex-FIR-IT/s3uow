from typing import TypeAlias

from .media import (
    AudioContent,
    BinaryContent,
    ImageContent,
    JsonContent,
    PdfContent,
    TextContent,
    UrlContent,
    VideoContent,
)

VideoOrAudio: TypeAlias = VideoContent | AudioContent

BinaryMedia: TypeAlias = (
    JsonContent
    | VideoContent
    | PdfContent
    | ImageContent
    | AudioContent
    | TextContent
    | BinaryContent
)

Media: TypeAlias = BinaryMedia | UrlContent
