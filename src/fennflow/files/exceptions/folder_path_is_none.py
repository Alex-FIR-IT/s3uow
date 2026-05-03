class FolderPathIsNoneException(Exception):
    """Exception raised when folder path is None."""

    def __init__(self, msg: str = "Folder path is None.") -> None:
        super().__init__(msg)
