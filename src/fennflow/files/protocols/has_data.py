from typing import Any, Protocol


class HasDataAttributeProtocol(Protocol):
    """Protocol for objects that expose a raw data attribute.

    Implement this protocol to indicate that an object holds
    arbitrary raw data accessible via the ``data`` attribute.

    Example:
        class MyContent:
            data: bytes = b"hello"
    """

    data: Any
