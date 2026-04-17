from typing import Protocol, Any


class HasExtensionPropertyProtocol(Protocol):
    @property
    def extension(self) -> str:
        ...