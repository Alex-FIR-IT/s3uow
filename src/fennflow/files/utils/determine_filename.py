from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fennflow.files.protocols.has_data_and_ext import (
        HasDataAndExtensionAttrProtocol,
    )


def get_determined_filename_by_obj(obj: HasDataAndExtensionAttrProtocol) -> str:
    """Generate a deterministic filename based on the object's content.

    The filename is computed as a SHA-256 hash of the object's `data`,
    followed by its `extension`. This guarantees that identical content
    will always produce the same filename.

    Args:
        obj: An object implementing `HasDataAndExtensionAttrProtocol`,
            providing:
                - data: file content (str | bytes | bytearray)
                - extension: file extension (e.g. ".txt", ".json")

    Returns:
        str: A deterministic filename in the format:
            "<sha256_hash><extension>"

    Raises:
        NotImplementedError: If `obj.data` is not str, bytes, or bytearray.

    """
    if isinstance(obj.data, str):
        data: bytes = obj.data.encode("utf-8")
    elif isinstance(obj.data, (bytes, bytearray)):
        data = obj.data
    else:
        raise NotImplementedError(
            f"Expected bytes or str, got {type(obj.data)=} instead."
        )

    return f"{hashlib.sha256(data).hexdigest()}{obj.extension}"


# noinspection PyUnusedLocal
def get_determined_filename_by_kwargs(
    *,
    data: str | bytes | bytearray,
    extension: str,
    **kwargs,
) -> str:
    """Generate a deterministic filename based on raw data and extension.

    This is a functional alternative to `get_determined_filename_by_obj`,
    accepting explicit keyword arguments instead of an object.

    Args:
        data (str | bytes | bytearray): File content used to compute the hash.
        extension (str): File extension (e.g. ".txt", ".json").
        **kwargs: Ignored. Present for API compatibility.

    Returns:
        str: A deterministic filename in the format:
            "<sha256_hash><extension>"

    Raises:
        NotImplementedError: If `data` is not a string.

    """
    if isinstance(data, str):
        prepared_data: bytes = data.encode("utf-8")
    elif isinstance(data, (bytes, bytearray)):
        prepared_data = data
    else:
        raise NotImplementedError(f"Expected bytes or str, got {type(data)=} instead.")
    return f"{hashlib.sha256(prepared_data).hexdigest()}{extension}"
