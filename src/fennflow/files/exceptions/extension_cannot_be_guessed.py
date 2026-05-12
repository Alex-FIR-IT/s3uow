from fennflow.files.exceptions.base import FileException


class ExtensionCannotBeGuessed(FileException):
    """Raised when the extension cannot be guessed from the filename."""
