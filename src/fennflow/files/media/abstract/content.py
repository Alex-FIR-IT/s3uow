from abc import ABC, abstractmethod
from typing import Any


class ContentPropertyAbstract(ABC):
    """Abstract mixin for media content classes that expose decoded content.

    Subclasses must implement ``content`` to define how raw bytes
    are decoded into a usable Python object.
    """

    @property
    @abstractmethod
    def content(self) -> Any:
        """Return the decoded content as a Python object.

        Returns:
            The decoded content in its native Python type
            (e.g. ``str`` for text, ``dict`` for JSON).
        """
        ...
