from __future__ import annotations

import logging
import mimetypes
import os
from abc import ABC
from typing import Any, ClassVar, Self

from pydantic import (
    BaseModel,
    ConfigDict,
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
from fennflow.files.protocols.has_data_and_ext_obj import (
    FileDataExtNamingFactoryProtocol,
)
from fennflow.files.utils.determine_filename import get_determined_filename_by_obj

logger = logging.getLogger(__name__)


class BaseContent(BaseModel, ABC):
    """Base class for all content types."""

    data: Any
    media_type: str | None = None
    filename: str | None = None
    kind: str = "base"
    folder_path: str | None = None

    @property
    def filepath(self) -> str:
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

    filename_factory: ClassVar[FileDataExtNamingFactoryProtocol] = (
        get_determined_filename_by_obj
    )
    model_config = ConfigDict(
        validate_assignment=True,
    )

    @model_validator(mode="after")
    def validate_filename_and_media_type(self) -> Self:
        if self.media_type and self.filename:
            valid_extensions = mimetypes.guess_all_extensions(
                self.media_type, strict=False
            )

            if valid_extensions and self.extension not in valid_extensions:
                logger.warning(
                    f"Mismatch: {self.filename} has {self.extension=}, "
                    f"but {self.media_type=} expects one of {valid_extensions}"
                )
        elif self.media_type:
            # noinspection PyArgumentList
            self.__dict__["filename"] = self.filename_factory()
        elif self.filename:
            guessed_media_type = mimetypes.guess_file_type(
                path=self.filename,
                strict=False,
            )[0]

            if guessed_media_type is None:
                raise MediaTypeCannotBeGuessed(filename=self.filename)
            self.__dict__["media_type"] = guessed_media_type
        else:
            raise FileNameAndMediaTypeBothNoneException()

        return self

    @property
    def extension(self) -> str:
        if self.filename:
            extension = os.path.splitext(self.filename)[-1].lower()

            if not extension:
                raise CannotParseExtensionException(filename=self.filename)

        elif self.media_type:
            logger.debug(
                f"Filename is not specified. "
                f"Trying to determine extension from {self.media_type=}"
            )
            guessed_extension = mimetypes.guess_extension(
                self.media_type,
                strict=False,
            )

            if guessed_extension is None:
                raise ExtensionCannotBeGuessed(
                    f"Cannot guess extension for {self.media_type=}. "
                    f"Please, specify filename explicitly."
                )
            extension = guessed_extension
            logger.debug(f"Determining has ended successfully. Got {extension=}")

        else:
            raise FileNameAndMediaTypeBothNoneException()

        return extension.strip()

    def get_metadata(self, exclude: set | None = None) -> dict:
        excluded_set = exclude or set()
        excluded_set.update({"data", "media_type"})

        metadata = self.model_dump(
            exclude_unset=True,
            exclude=excluded_set,
        )
        logger.debug(f"Generated metadata for {self=}: {metadata=}")

        return metadata
