from typing import TypeAlias

from .media import (
    AudioContent,
    BinaryContent,
    DocumentContent,
    ImageContent,
    JsonContent,
    TextContent,
    UrlContent,
    VideoContent,
)

VideoOrAudio: TypeAlias = VideoContent | AudioContent

BinaryMedia: TypeAlias = (
    JsonContent
    | VideoContent
    | DocumentContent
    | ImageContent
    | AudioContent
    | TextContent
    | BinaryContent
)

Media: TypeAlias = BinaryMedia | UrlContent
