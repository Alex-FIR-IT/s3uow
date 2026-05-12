from .binary_content import BinaryContent


class VideoContent(BinaryContent):
    """Media content representing a video file.

    Attributes:
        duration: Duration of the video in seconds.
        height: Height of the video in pixels.
        width: Width of the video in pixels.
    """

    duration: int | None = None
    height: int | None = None
    width: int | None = None
