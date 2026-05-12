from fennflow.files.exceptions.base import FileException


class FilenameIsNoneException(FileException):
    """Exception raised when filename is None."""

    def __init__(self, msg: str = "Filename is None.") -> None:
        super().__init__(msg)
