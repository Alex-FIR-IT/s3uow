from fennflow._base_exception import FennFlowException


class BaseBackendException(FennFlowException):
    """Base exception for all FennFlow backend errors."""


class RecordAlreadyExistsException(BaseBackendException):
    """Raised when attempting to add a record that already exists in the backend."""
