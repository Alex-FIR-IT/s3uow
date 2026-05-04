from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from fennflow.files.protocols.has_data_and_ext import (
        HasDataAndExtensionAttrProtocol,
    )


class FilenameFactoryProtocol(Protocol):
    """Callable that generates a filename from a media object.

    Args:
        obj: An object exposing both ``data`` and ``extension``.

    Returns:
        A filename string derived from the object's data and extension.
    """

    def __call__(self, obj: "HasDataAndExtensionAttrProtocol") -> str: ...
