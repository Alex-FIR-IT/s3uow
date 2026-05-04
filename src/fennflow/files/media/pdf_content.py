from typing import Literal

from .binary_content import BinaryContent


class PdfContent(BinaryContent):
    """Media content representing a PDF file."""

    kind: Literal["pdf"] = "pdf"
