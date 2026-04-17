import hashlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from s3uow.files.protocols.has_data_and_ext import HasDataAndExtensionAttrProtocol


def get_determined_filename_by_obj(obj: "HasDataAndExtensionAttrProtocol") -> str:
    if isinstance(obj.data, str):
        data: bytes = obj.data.encode("utf-8")
    elif isinstance(obj.data, (bytes, bytearray)):
        data = obj.data
    else:
        raise NotImplementedError(f"Expected bytes or str, got {type(obj.data)=} instead.")
    
    return f"{hashlib.sha256(data).hexdigest()}{obj.extension}"


# noinspection PyUnusedLocal
def get_determined_filename_by_kwargs(
        *,
        data: str | bytes | bytearray,
        extension: str,
        **kwargs,
) -> str:
    if isinstance(data, str):
        data: bytes = data.encode("utf-8")
    else:
        raise NotImplementedError(f"Expected bytes or str, got {type(data)=} instead.")

    return f"{hashlib.sha256(data).hexdigest()}{extension}"