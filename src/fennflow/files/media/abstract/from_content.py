from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from fennflow._sentinel import OMIT, Omittable

if TYPE_CHECKING:
    from typing_extensions import Self


class FromContentAbstract(ABC):
    """Abstract mixin for media content classes that can be created from raw data.

    Subclasses must implement ``from_content()`` to define how
    raw data is converted into a media content instance.
    """

    @classmethod
    @abstractmethod
    def from_content(
        cls,
        data: Any,
        media_type: str,
        encoding: str = "utf-8",
        filename: Omittable[str] = OMIT,
        **kwargs: Any,
    ) -> Self:
        """Create a media content instance from raw data.

        Args:
            data: The raw data to create the content from.
            media_type: The MIME type of the content (e.g. ``"text/plain"``).
            encoding: The text encoding. Defaults to ``"utf-8"``.
            filename: The name of the file. Will be generated if not provided.
            kwargs: Any additional keyword arguments to pass to the constructor.

        Returns:
            A new instance of the media content class.
        """
        ...
