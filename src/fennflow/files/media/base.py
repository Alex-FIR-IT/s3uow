from __future__ import annotations

import logging
import mimetypes
import os
from abc import ABC
from hashlib import sha256
from typing import TYPE_CHECKING, Any, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

from fennflow._path import Path
from fennflow.files.exceptions.cannot_parse_extension import (
    CannotParseExtensionException,
)
from fennflow.files.exceptions.extension_cannot_be_guessed import (
    ExtensionCannotBeGuessed,
)
from fennflow.files.exceptions.filename_and_mediatype_both_none import (
    FileNameAndMediaTypeBothNoneException,
)
from fennflow.files.exceptions.filename_is_none import FilenameIsNoneException
from fennflow.files.exceptions.folder_path_is_none import FolderPathIsNoneException
from fennflow.files.exceptions.media_type_cannot_be_guessed import (
    MediaTypeCannotBeGuessed,
)

if TYPE_CHECKING:
    from fennflow._new_types import Filepath

logger = logging.getLogger(__name__)


class BaseContent(BaseModel, ABC):
    """Base class for all content types."""

    data: Any
    filename: str
    media_type: str
    kind: str = "base"
    folder_path: str | None = None
    extra_metadata: dict[str, str] = Field(default_factory=dict)

    @property
    def filepath(self) -> Filepath:
        if self.folder_path is None:
            raise FolderPathIsNoneException(
                f"Cannot determine filepath for {self.filename=}. Folder path is None."
            )
        elif self.filename is None:
            raise FilenameIsNoneException(
                f"Cannot determine filepath for file in {self.folder_path=}. "
                f"Filename is None."
            )
        return Path.join_path(self.folder_path, self.filename)

    model_config = ConfigDict(
        validate_assignment=True,
    )

    @model_validator(mode="before")
    @classmethod
    def collect_extra_to_metadata(cls, data: dict) -> dict:
        allowed_fields = cls.model_fields.keys()

        extra = {}

        for key, value in data.items():
            if key not in allowed_fields:
                extra[key] = str(value)

        data["extra_metadata"] = {**data.get("extra_metadata", {}), **extra}

        return data

    @model_validator(mode="before")
    @classmethod
    def validate_filename_and_media_type(cls, data):
        filename = data.get("filename")
        media_type = data.get("media_type")

        if media_type and filename:
            pass
        elif media_type:
            data["filename"] = sha256(data["data"]).hexdigest()
        elif filename:
            guessed_media_type = mimetypes.guess_type(filename, strict=False)[0]
            if guessed_media_type is None:
                raise MediaTypeCannotBeGuessed(filename=filename)
            data["media_type"] = guessed_media_type

        else:
            raise FileNameAndMediaTypeBothNoneException()

        return data

    @model_validator(mode="after")
    def ensure_filename_has_ext(self) -> Self:
        ext = os.path.splitext(self.filename)[-1]

        if not ext:
            guessed_extension = mimetypes.guess_extension(
                self.media_type,
                strict=False,
            )

            if guessed_extension is None:
                raise ExtensionCannotBeGuessed(
                    f"Cannot guess extension for {self.media_type=}. "
                    f"Please, specify filename explicitly."
                )

            self.__dict__["filename"] = f"{self.filename}{guessed_extension}"
        return self

    @model_validator(mode="after")
    def warn_about_media_type_and_ext_mismatch(self) -> Self:
        valid_extensions = mimetypes.guess_all_extensions(self.media_type, strict=False)

        if valid_extensions and self.extension not in valid_extensions:
            logger.warning(
                f"Mismatch: {self.filename} has {self.extension=}, "
                f"but {self.media_type=} expects one of {valid_extensions}"
            )

        return self

    @property
    def extension(self) -> str:
        extension = os.path.splitext(self.filename)[-1].lower()

        if not extension:
            raise CannotParseExtensionException(filename=self.filename)
        return extension.strip()

    def get_metadata(self, exclude: set | None = None) -> dict:
        excluded_set = exclude or set()
        excluded_set.update({"data", "media_type", "extra_metadata"})

        metadata = self.model_dump(
            exclude_unset=True,
            exclude=excluded_set,
        )
        logger.debug(f"Generated metadata for {self=}: {metadata=}")

        return {**self.extra_metadata, **metadata}
