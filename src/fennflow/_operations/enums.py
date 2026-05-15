from enum import IntEnum, auto


class OperationTypeEnum(IntEnum):
    """Enum for operation types."""

    CREATE = auto()
    PUT = auto()
    GET = auto()
    DELETE = auto()


class OperationStatusEnum(IntEnum):
    """Enum for operation status."""

    PENDING = auto()
    UPLOADED = auto()
    FAILED = auto()
    COMPENSATION_FAILED = auto()
    DELETED = auto()
