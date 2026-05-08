import os.path


class MediaTypeCannotBeGuessed(Exception):
    """Raised when the media type cannot be guessed from the filename."""

    def __init__(self, filename: str):
        ext = os.path.splitext(filename)[1]

        if ext:
            msg = (
                f"Cannot guess media type for {filename=}. "
                f"Please, specify media_type explicitly."
            )
        else:
            msg = (
                "Cannot guess media type. "
                "Please, specify media_type or filename with extension explicitly."
            )
        super().__init__(msg)
        self.filename = filename
