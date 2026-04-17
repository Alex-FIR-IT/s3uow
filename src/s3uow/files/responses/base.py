from typing import Iterator, Sequence, overload

from pydantic import BaseModel, field_validator

from s3uow.files.media import TextContent, ImageContent, AudioContent, VideoContent, PdfContent
from s3uow.files.types import Media


class MediaResponse(BaseModel):
    media: Sequence[Media]

    @field_validator("media", mode="before")
    @classmethod
    def convert_strs_to_files(cls, media: Sequence[Media | str]) -> tuple[Media, ...]:
        return tuple(
            (
                TextContent.from_text(file_or_str)
                if isinstance(file_or_str, str)
                else file_or_str
            )
            for file_or_str in media
        )

    @overload
    def filter[T: Media](self, typ: type[T]) -> tuple[T, ...]: ...

    @overload
    def filter[T: Media](self, *types: type[T]) -> tuple[T, ...]: ...

    def filter(self, *types):
        return tuple(file for file in self.media if isinstance(file, types))

    def filter_by_media_type(self, *media_types: str) -> tuple[Media, ...]:
        return tuple(file for file in self.media if file.media_type in media_types)

    @property
    def images(self) -> "tuple[ImageContent, ...]":
        return self.filter(ImageContent)

    @property
    def videos(self) -> "tuple[VideoContent, ...]":
        return self.filter(VideoContent)

    @property
    def texts(self) -> "tuple[TextContent, ...]":
        return self.filter(TextContent)

    @property
    def audios(self) -> "tuple[AudioContent, ...]":
        return self.filter(AudioContent)

    @property
    def pdfs(self) -> "tuple[PdfContent, ...]":
        return self.filter(PdfContent)

    def __iter__(self) -> Iterator[Media]:
        return iter(self.media)

    def __getitem__(self, item):
        return self.media[item]
