from .media import VideoContent, PdfContent, ImageContent, AudioContent, BinaryContent
from .media.text_content import TextContent
from .types import Media


def content_factory(media_type: str, **data,) -> Media:
    data["media_type"] = media_type

    if media_type.startswith("text"):
        return TextContent.model_validate(data)
    if media_type.startswith("video/"):
        return VideoContent.model_validate(data)
    if media_type.startswith("audio/"):
        return AudioContent.model_validate(data)
    if media_type.startswith("image/"):
        return ImageContent.model_validate(data)
    if media_type == "application/pdf":
        return PdfContent.model_validate(data)

    return BinaryContent.model_validate(data)
