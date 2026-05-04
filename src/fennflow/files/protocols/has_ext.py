from typing import Protocol


class HasExtensionPropertyProtocol(Protocol):
    """Protocol for objects that expose a file extension property.

    Implement this protocol to indicate that an object has an ``extension``
    property returning the file extension including the leading dot.

    Example:
        class MyFile:
            @property
            def extension(self) -> str:
                return ".txt"
    """

    @property
    def extension(self) -> str:
        """Return the file extension including the leading dot (e.g. ``.txt``)."""
        ...
