from abc import ABC, abstractmethod
from typing import Any, Self


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
    ) -> Self:
        """Create a media content instance from raw data.

        Args:
            data: The raw data to create the content from.
            media_type: The MIME type of the content (e.g. ``"text/plain"``).
            encoding: The text encoding. Defaults to ``"utf-8"``.

        Returns:
            A new instance of the media content class.
        """
        ...
