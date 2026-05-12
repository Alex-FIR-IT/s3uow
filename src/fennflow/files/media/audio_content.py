from .binary_content import BinaryContent


class AudioContent(BinaryContent):
    """Media content representing an audio file.

    Attributes:
        duration: Duration of the audio in seconds, if known.
    """

    duration: int | None = None
