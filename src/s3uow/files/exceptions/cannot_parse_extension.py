from .base import FileException

class CannotParseExtensionException(FileException):
    """Raised when trying to parse an extension from a filename"""

    def __init__(self, filename: str):
        msg = f"Cannot parse an extension from a {filename=}! Are you sure that file has extension in its name?"
        super().__init__(msg)
        self.filename = filename
