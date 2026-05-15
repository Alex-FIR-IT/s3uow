from fennflow._base_exception import FennFlowException


class BaseBackendException(FennFlowException):
    """Base exception for all FennFlow backend errors."""


class RecordAlreadyExistsException(BaseBackendException):
    """Raised when attempting to add a record that already exists in the backend."""


class RecordLockedException(BaseBackendException):
    """Raised when attempting to modify a record that is currently locked."""

    def __init__(self, storage_path: str):
        msg = (
            f"The record for the file at path '{storage_path}' is currently locked "
            "by another session. "
            "Please try again later."
        )
        super().__init__(msg)
