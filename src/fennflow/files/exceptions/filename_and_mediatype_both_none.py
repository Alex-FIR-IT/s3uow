from fennflow.files.exceptions.base import FileException


class FileNameAndMediaTypeBothNoneException(FileException):
    """Exception raised when both media type and filename are None."""

    def __init__(
        self,
        msg: str = "Media type or filename cannot be both None! "
        "Please, pass either media_type or filename.",
    ) -> None:
        super().__init__(msg)
