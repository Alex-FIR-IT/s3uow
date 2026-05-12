from enum import IntEnum, auto


class OnConflictDoEnum(IntEnum):
    """Actions to take when a conflict occurs."""

    DO_NOTHING = auto()
    REPLACE = auto()
    RAISE = auto()
