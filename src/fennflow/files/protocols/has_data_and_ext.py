from .has_data import HasDataAttributeProtocol
from .has_ext import HasExtensionPropertyProtocol


class HasDataAndExtensionAttrProtocol(
    HasDataAttributeProtocol,
    HasExtensionPropertyProtocol,
):
    """Protocol for objects that expose both a data attribute and an extension property.

    Used as a type constraint where both ``data`` and ``extension`` are required.

    Example:
        class MyFile:
            data: bytes = b"hello"

            @property
            def extension(self) -> str:
                return ".txt"
    """
