from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from s3uow.files.protocols.has_data_and_ext import HasDataAndExtensionAttrProtocol


class FileDataExtNamingFactoryProtocol(Protocol):

    def __call__(self , obj: "HasDataAndExtensionAttrProtocol") -> str:...