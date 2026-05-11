from enum import IntEnum, auto


class ReconcileFrequencyEnum(IntEnum):
    """Controls how often reconciliation is performed.

    Attributes:
        ON_START_APP: Reconcile once per process lifetime.
        ON_SESSION_START: Reconcile on every ``UnitOfWork.__aenter__`` call.
        NEVER: Disable reconciliation.
    """

    ON_START_APP = auto()
    ON_SESSION_START = auto()
    NEVER = auto()


class ReconcileStrategyEnum(IntEnum):
    """Defines how reconciliation updates existing data.

    Attributes:
        FILL_IF_EMPTY: Reconcile only if the backend is empty.
        REPLACE: Reset all backend data before reconciling.
        INSERT_MISSING: Insert missing data while keeping existing data intact.
    """

    FILL_IF_EMPTY = auto()
    REPLACE = auto()
    INSERT_MISSING = auto()
