from enum import StrEnum, auto


class OperationTypeEnum(StrEnum):
    """Enum for operation types."""

    PUT = auto()
    GET = auto()
    DELETE = auto()
