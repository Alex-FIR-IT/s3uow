from fennflow._base_exception import FennFlowException


class ReconcileFailedException(FennFlowException):
    """Raised when a reconciliation failed."""

    def __init__(self, message="Reconcile failed", *args):
        super().__init__(message, *args)
