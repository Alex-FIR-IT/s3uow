from typing import Literal

from .binary_content import BinaryContent


class PdfContent(BinaryContent):
    kind: Literal["pdf"] = "pdf"
