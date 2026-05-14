from fennflow._base_exception import FennFlowException


class ReconcileFailedException(FennFlowException):
    def __init__(self, message="Reconcile failed", *args):
        super().__init__(message, *args)
