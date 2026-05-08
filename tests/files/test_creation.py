import logging
import mimetypes

import pytest

from fennflow.files import BinaryContent
from fennflow.files.exceptions.extension_cannot_be_guessed import (
    ExtensionCannotBeGuessed,
)
from fennflow.files.exceptions.media_type_cannot_be_guessed import (
    MediaTypeCannotBeGuessed,
)


def test_only_filename_specified():
    file = BinaryContent(data=b"hi", filename="test.txt")
    assert file.media_type == "text/plain"

    with pytest.raises(MediaTypeCannotBeGuessed):
        file = BinaryContent(data=b"hi", filename="test")


def test_only_media_type_specified():
    file = BinaryContent(data=b"hi", media_type="text/plain")
    assert file.extension == ".txt"

    with pytest.raises(ExtensionCannotBeGuessed):
        file = BinaryContent(data=b"hi", media_type="kfjdkfdj")


def test_both_filename_and_media_type_specified(caplog):
    file = BinaryContent(data=b"hi", filename="test.txt", media_type="text/plain")
    assert file.filename == "test.txt"
    assert file.media_type == "text/plain"
    assert file.extension == ".txt"

    with caplog.at_level(logging.WARNING):
        file = BinaryContent(
            data=b"hi", filename="test.txt", media_type="application/pdf"
        )

    assert "mismatch" in caplog.text.lower()


def test_extension_appended_to_filename():
    media_type = "text/plain"
    guessed_extension = mimetypes.guess_extension(media_type)

    file = BinaryContent(data=b"hi", filename="test", media_type=media_type)
    assert file.filename == f"test{guessed_extension}"
    assert file.media_type == media_type
    assert file.extension == guessed_extension


def test_extra_metadata():
    file = BinaryContent(data=b"hi", filename="file.txt", price=5)
    assert file.extra_metadata["price"] == "5"

    file2 = BinaryContent.model_validate(file.model_dump())
    assert file.extra_metadata["price"] == "5"
    assert file == file2
