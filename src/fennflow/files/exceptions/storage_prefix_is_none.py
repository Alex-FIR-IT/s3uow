from fennflow.files.exceptions.base import FileException


class StoragePrefixIsNoneException(FileException):
    """Exception raised when storage_prefix is None."""

    def __init__(self, msg: str = "Storage path is None.") -> None:
        super().__init__(msg)
