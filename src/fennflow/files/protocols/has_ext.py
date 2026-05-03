from typing import Protocol


class HasExtensionPropertyProtocol(Protocol):
    @property
    def extension(self) -> str: ...
