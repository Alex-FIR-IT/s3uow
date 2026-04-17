from enum import StrEnum, auto


class Modalities(StrEnum):
    TEXT = auto()
    IMAGE = auto()
    AUDIO = auto()
    VIDEO = auto()
    PDF = auto()
    UNKNOWN = auto()
