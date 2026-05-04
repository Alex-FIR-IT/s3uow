from typing import Literal

from .base import BaseContent


class UrlContent(BaseContent):
    """Media content representing a URL.

    Attributes:
        data: The URL string.
    """

    data: str
    kind: Literal["url"] = "url"
