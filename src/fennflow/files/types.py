from typing import TypeAlias

from .media import (
    AudioContent,
    BinaryContent,
    ImageContent,
    JsonContent,
    DocumentContent,
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
