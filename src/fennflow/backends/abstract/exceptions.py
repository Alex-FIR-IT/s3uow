class BaseBackendException(Exception):
    """Base exception for all FennFlow backend errors."""


class RecordAlreadyExistsException(BaseBackendException):
    """Raised when attempting to add a record that already exists in the backend."""
