from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, TypeVar, overload

from fennflow.files.media import (
    AudioContent,
    DocumentContent,
    ImageContent,
    TextContent,
    VideoContent,
)
from fennflow.files.types import Media

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from typing_extensions import Self

T = TypeVar("T", bound=Media)


@dataclass(slots=True)
class MediaResponse:
    """Response object containing a collection of media items.

    Returned by repository read operations such as ``GetRepository.get()``.

    Attributes:
        media: A tuple of media items retrieved from storage.

    Example:
        response = await uow.user_files.at("user1/").get("file.txt")
        for item in response.media:
            print(item.data)
    """

    media: tuple[Media, ...] = field(default_factory=tuple)

    def __post_init__(self):
        self.media = tuple(
            TextContent.from_content(item) if isinstance(item, str) else item
            for item in self.media
        )

    @classmethod
    def join(cls, iterable: Iterable[Self]) -> Self:
        """Combine multiple MediaResponse instances into one.

        Args:
            iterable: An iterable of MediaResponse instances to combine.

        Returns:
            A new MediaResponse containing all media from the given responses.

        Example:
            combined = MediaResponse.join([response1, response2])
        """
        return cls(media=tuple(file for response in iterable for file in response))

    @overload
    def filter(self, typ: type[T]) -> tuple[T, ...]: ...

    @overload
    def filter(self, *types: type[T]) -> tuple[T, ...]: ...

    def filter(self, *types):
        """Filter media items by type.

        Args:
            *types: One or more media types to filter by.

        Returns:
            A tuple of media items that are instances of the given types.

        Example:
            images = response.filter(ImageContent)
            text_and_json = response.filter(TextContent, JsonContent)
        """
        return tuple(file for file in self.media if isinstance(file, types))

    def filter_by_media_type(self, *media_types: str) -> tuple[Media, ...]:
        """Filter media items by MIME type string.

        Args:
            *media_types: One or more MIME type strings to filter
                by (e.g. ``"text/plain"``).

        Returns:
            A tuple of media items whose ``media_type`` matches one of the given types.

        Example:
            text_and_json = response.filter_by_media_type(
                                        "text/plain",
                                        "application/json"
                                        )
        """
        return tuple(file for file in self.media if file.media_type in media_types)

    @property
    def images(self) -> tuple[ImageContent, ...]:
        return self.filter(ImageContent)

    @property
    def videos(self) -> tuple[VideoContent, ...]:
        return self.filter(VideoContent)

    @property
    def texts(self) -> tuple[TextContent, ...]:
        return self.filter(TextContent)

    @property
    def audios(self) -> tuple[AudioContent, ...]:
        return self.filter(AudioContent)

    @property
    def documents(self) -> tuple[DocumentContent, ...]:
        return self.filter(DocumentContent)

    def __iter__(self) -> Iterator[Media]:
        return iter(self.media)

    def __getitem__(self, item) -> Media:
        return self.media[item]

    def __len__(self) -> int:
        return len(self.media)
