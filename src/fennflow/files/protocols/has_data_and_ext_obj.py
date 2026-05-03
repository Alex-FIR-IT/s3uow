from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from fennflow.files.protocols.has_data_and_ext import (
        HasDataAndExtensionAttrProtocol,
    )


class FileDataExtNamingFactoryProtocol(Protocol):
    def __call__(self, obj: "HasDataAndExtensionAttrProtocol") -> str: ...
