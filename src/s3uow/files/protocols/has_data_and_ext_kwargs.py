from typing import Protocol


class RequireDataAndExtensionAttrProtocol(Protocol):

    def __call__(self ,*, data: str | bytes | bytearray, extension: str,) -> str:...