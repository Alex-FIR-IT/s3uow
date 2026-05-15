from fennflow._base_exception import FennFlowException


class BaseRepositoryException(FennFlowException):
    """Base exception for repository-related errors."""


class FilepathsCollisionError(BaseRepositoryException):
    """Exception raised when several files have the same filepath."""

    def __init__(
        self,
        *args,
        msg: str = (
            "Filepath collision detected: multiple files share the same filepath. "
            "Ensure all files passed to this method have unique filepaths."
        ),
        **kwargs,
    ) -> None:
        super().__init__(msg, *args, **kwargs)
