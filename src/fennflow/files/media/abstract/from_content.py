from abc import ABC, abstractmethod
from typing import Any, Self


class FromContentAbstract(ABC):
    @classmethod
    @abstractmethod
    def from_content(
        cls,
        data: Any,
        encoding: str = "utf-8",
        media_type: str = "text/plain",
    ) -> Self: ...
