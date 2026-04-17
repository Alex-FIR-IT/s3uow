from typing import Literal

from .base import BaseContent


class UrlContent(BaseContent):
    data: str
    kind: Literal["url"] = "url"
