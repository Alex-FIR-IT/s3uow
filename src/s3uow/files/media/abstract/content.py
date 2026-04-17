from abc import ABC, abstractmethod
from typing import Any


class ContentPropertyAbstract(ABC):

    @property
    @abstractmethod
    def content(self) -> Any:
        ...