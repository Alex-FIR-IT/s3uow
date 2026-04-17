class MediaTypeCannotBeGuessed(Exception):
    """Raised when the media type cannot be guessed from the filename."""

    def __init__(self, filename: str):
        msg = f"Cannot guess media type for {filename=}. Please, specify media_type explicitly."
        super().__init__(msg)
        self.filename = filename
