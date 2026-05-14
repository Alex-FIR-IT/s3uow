1.

from __future__ import annotations

from typing import TYPE_CHECKING

from fennflow._path import Path

from .base import BaseRepository

if TYPE_CHECKING:
from typing_extensions import Self

    from fennflow._new_types import StoragePath

class AtRepository(BaseRepository):
"""Repository mixin that adds path navigation capabilities.

    Allows scoping operations to a specific path within the namespace
    using the ``at()`` method.

    Example:
        await uow.user_files.at("user1/").put(file)
    """

    def _join_path(self, *paths: str) -> StoragePath:
        """Join the current path with one or more path segments.

        Args:
            *paths: Path segments to append to the current path.

        Returns:
            The joined and normalized path string.
        """
        return Path.join_path(self._path, *paths)

    def at(self, path: str) -> Self:
        """Return a new repository instance scoped to the given path.

        Args:
            path: Path to scope the repository to, relative to the current path.

        Returns:
            A new repository instance with the updated path.

        Example:
            storage = uow.user_files.at("user1/")
            await storage.put(file)
        """
        new_path = self._join_path(path)

        return self.__class__(self._uow, new_path, repo_extra=self.repo_extra)

    @property
    def cwd(self) -> str:
        """Return the current working path.

        Returns:
            The normalized current path string.
        """
        return Path.normalize_folder(self._path)

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
from fennflow.repositories.fields.base import RepoExtra
from fennflow.uow.core import UnitOfWork

class BaseRepository:  # noqa: B903
"""Base class for all FennFlow repositories.

    Provides access to the UnitOfWork, current path, and connector configuration.
    Not meant to be used directly — use mixins like PutRepository, GetRepository etc.

    Args:
        uow: The UnitOfWork instance managing this repository's session.
        path: The current working path within the namespace.
        repo_extra: Connector-specific configuration including namespace.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        path: str,
        repo_extra: RepoExtra,
    ):
        self._uow = uow
        self._path = path
        self.repo_extra = repo_extra

from __future__ import annotations

from fennflow._operations.context.delete import DeleteContext
from fennflow._operations.dto import OperationRecord
from fennflow._operations.enums import OperationStatusEnum, OperationTypeEnum

from .at import AtRepository

class DeleteRepository(AtRepository):
"""Repository mixin for deleting files from storage.

    Implements Saga-based deletion with automatic compensation on failure.
    """

    async def delete(self, path: str, **provider_extra) -> bool:
        """Delete a file from storage.

        Args:
            path: Path to the file relative to the current directory.
            **provider_extra: Additional kwargs forwarded to the connector.

        Returns:
            True if the file was deleted, False if it did not exist.

        """
        storage_path = self._join_path(path)
        operation = await self._uow.backend.get(storage_path)

        if operation is None or not operation.is_visible(self._uow._session_id):
            return False

        context = DeleteContext(
            to_storage_path=self._join_path(
                "tmp",
                f"session_id_{operation.session_id}",
                f"operation_id_{operation.session_id}",
                self._path,
                path,
            ),
            to_namespace=self.repo_extra["namespace"],
        )

        operation = OperationRecord(
            operation_type=OperationTypeEnum.DELETE,
            status=OperationStatusEnum.PENDING,
            storage_path=operation.storage_path,
            context=context,
            session_id=self._uow._session_id,
            repo_extra=self.repo_extra,
        )
        await self._uow.backend.add(operation)

        await self._uow._operation_executor.execute(
            operation,
            **provider_extra,
        )
        await self._uow.backend.flush()
        return True

from __future__ import annotations

import asyncio

from fennflow.files.responses.base import MediaResponse
from fennflow.repositories.at import AtRepository

class GetRepository(AtRepository):
"""Repository for retrieving a file from storage within the current scope.

    This method returns a `MediaResponse` object containing the requested file,
    if it exists according to the backend (source of truth).

    **Example**::

        response = await uow.user_files.at("user1/").get("file.txt")
        if response:
            file = response[0]

    **Behavior**:

    - The backend is treated as the source of truth
    - If the file is not present in the backend, the storage is NOT queried
    - If the file exists in the backend,
    it is fetched from the storage via the connector

    **Notes**:

    - This method is read-only and does not participate in transaction flows (no saga)
    - No network request is made if the backend does not contain the file
    - Storage and backend may become inconsistent
      (e.g. after restart with InMemoryBackend);
      in such cases, use a reconcile mechanism to resync state.
      (<add_link_here on wiki>)

    """

    async def get(self, *paths: str, **provider_extra) -> MediaResponse:
        """Retrieve a file from storage within the current scope.

        Args:
            *paths (str):
                Relative file's paths within the scoped repository

            **provider_extra (Any):
                Additional provider-specific parameters passed directly to the connector
                (e.g. S3 `get_object` arguments)

        Returns:
            MediaResponse:
                - `MediaResponse(media=(...))` if the file exists
                - `MediaResponse()` (empty) if the file does not exist
        """
        tasks = []
        for path in paths:
            storage_path = self._join_path(path)
            operation = await self._uow.backend.get(storage_path)

            if operation and operation.is_visible(self._uow._session_id):
                tasks.append(
                    self._uow.connector.get(
                        storage_path=storage_path,
                        repo_extra=self.repo_extra,
                        **provider_extra,
                    )
                )

        if tasks:
            results = await asyncio.gather(*tasks)
            return MediaResponse.join(results)

        return MediaResponse()

from __future__ import annotations

from fennflow._sentinel import OMIT, Omittable
from fennflow.files.responses.list import ListResponse
from fennflow.repositories.at import AtRepository

class ListRepository(AtRepository):
"""Repository for retrieving a files from storage within the current scope."""

    async def list(
            self,
            prefix: str = "",
            continuation_token: Omittable[str] = OMIT,
            limit: int = 1000,
            ) -> ListResponse:
        """Uploads files under the current path, optionally filtered by prefix.

        Files are visible if they are uploaded (committed) or pending within the
        current session. Pending files from other sessions are not returned.

        Args:
            prefix: Sub-path to filter results. Appended to the current ``at()``
                path. Defaults to ``""`` (list everything under the current path).
            continuation_token: Opaque token returned by a previous call to
                continue paginating.
            limit: Maximum number of storage_paths to return. Defaults to ``1000``.

        Returns:
            ListResponse: A container of storage_paths matching the query. Includes
                a ``continuation_token`` if more results are available, otherwise
                ``None``.

        Example::

             async with UOW() as uow:
                 await uow.files.at("folder1/").put(file1, file2, file3)
                 page = await uow.files.at("folder1/").list(limit=2)

                 next_page = await uow.files.at("folder1/").list(
                     limit=2,
                     continuation_token=page.continuation_token,
                 )
        """
        storage_prefix = self._join_path(prefix)

        operation_page = await self._uow.backend.get_visible(
            prefix=storage_prefix,
            continuation_token=continuation_token,
            limit=limit,
            session_id=self._uow._session_id,
            )

        return ListResponse(
            storage_paths=tuple(op.storage_path for op in operation_page),
            continuation_token=operation_page.continuation_token,
            )

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from fennflow._operations.context.put import PutContext
from fennflow._operations.dto import OperationRecord
from fennflow._operations.enums import OperationStatusEnum, OperationTypeEnum
from fennflow.backends.exceptions import RecordAlreadyExistsException
from fennflow.repositories.at import AtRepository

if TYPE_CHECKING:
from fennflow.files.types import BinaryMedia

class PutRepository(AtRepository):
"""Repository for uploading (creating) files in the storage.

    This repository implements the "put" operation, which uploads new files
    to the configured storage (e.g. S3) within the current Unit of Work.

    **Example**::

        file1 = TextContent.from_content("This is the first file.")
        await uow.user_files.at("user1/").put(file1)

    **Behavior**:

    - Each file is registered in the backend as a pending operation
    - Files are uploaded via the connector
    - Backend commit is executed on uow.commit

    **Raises**:
        FileAlreadyExistError: If a file with the same path already exists in a backend

    **For other behaviors**:

    - To overwrite existing files, use ReplaceRepository (add wiki)
    - To put or replace, use PutOrReplaceRepository (add wiki)

    """

    async def put(
            self,
            *files: BinaryMedia,
            **provider_extra,
            ) -> None:
        tasks = []
        for file in files:
            file._storage_prefix = self.cwd

            operation = await self._uow.backend.get(storage_path=file.storage_path)

            if operation:
                raise RecordAlreadyExistsException()

            operation = OperationRecord(
                operation_type=OperationTypeEnum.PUT,
                status=OperationStatusEnum.PENDING,
                storage_path=file.storage_path,
                context=PutContext(file=file),
                session_id=self._uow._session_id,
                repo_extra=self.repo_extra,
                )

            await self._uow.backend.add(operation)
            tasks.append(
                self._uow._operation_executor.execute(
                    operation,
                    **provider_extra,
                    ),
                )
        await self._uow.backend.flush()
        await asyncio.gather(*tasks)

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypedDict, TypeVar, overload

if TYPE_CHECKING:
from fennflow._new_types import Namespace

RepoType = TypeVar("RepoType")

class RepoExtra(TypedDict):
"""Base configuration passed to every repository instance.

    Attributes:
        namespace: The storage namespace (e.g. S3 bucket name).
    """

    namespace: Namespace

class RepoField(Generic[RepoType]):
"""A descriptor that lazily initializes a repository instance on a UnitOfWork.

    Args:
        repo_cls: The repository class to instantiate.
        namespace: The storage namespace (e.g. S3 bucket name) for this repository.

    Example:
        class UOW(UnitOfWork):
            user_files = RepoField(UserFiles, namespace="user-files")

    """

    def __init__(
        self,
        repo_cls: type[RepoType],
        *,
        namespace: Namespace,
    ):
        self.repo_cls = repo_cls
        self.repo_extra: RepoExtra = {"namespace": namespace}

    def __set_name__(
        self,
        owner,
        name,
    ):
        self.name = name

    @overload
    def __get__(
        self,
        instance: None,
        owner,
    ) -> RepoField[RepoType]: ...

    @overload
    def __get__(
        self,
        instance,
        owner,
    ) -> RepoType: ...

    def __get__(
        self,
        instance,
        owner,
    ):
        if instance is None:
            return self

        repo = instance.__dict__.get(self.name)
        if repo is None:
            repo = self.repo_cls(
                uow=instance,
                path="/",
                repo_extra=self.repo_extra,
            )
            instance.__dict__[self.name] = repo

        return repo

from __future__ import annotations

from typing import TYPE_CHECKING

from fennflow.repositories.fields.base import RepoField, RepoType

from .base import RepoExtra

if TYPE_CHECKING:
from fennflow._new_types import BucketName

class S3Extra(RepoExtra):
"""Configuration parameters for S3-backed repository fields.

    bucket_name is an alias for Namespace from fennflow._new_types.
    """

    bucket_name: BucketName

def S3RepoField(
repo_cls: type[RepoType],
bucket_name: BucketName,
) -> RepoField[RepoType]:
"""Create a RepoField configured for S3 storage.

    Args:
        repo_cls: The repository class to instantiate.
        bucket_name: alias for RepoField.namespace.

    Returns:
        A configured RepoField bound to the given repository class.

    **Example**::

        class UOW(UnitOfWork):
            user_files = S3RepoField(UserFiles, bucket_name="my-bucket")

    """
    return RepoField(
        repo_cls,
        namespace=bucket_name,
    )

2.

from __future__ import annotations

import logging
import mimetypes
import os
from abc import ABC
from functools import total_ordering
from hashlib import sha256
from typing import TYPE_CHECKING, Any

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
from fennflow.files.exceptions.media_type_cannot_be_guessed import (
MediaTypeCannotBeGuessedException,
)
from fennflow.files.exceptions.storage_prefix_is_none import (
StoragePrefixIsNoneException,
)

if TYPE_CHECKING:
from typing_extensions import Self

    from fennflow._new_types import StoragePath

logger = logging.getLogger(__name__)

@total_ordering
class BaseContent(BaseModel, ABC):
"""Base class for all content types."""

    data: Any
    filename: str
    media_type: str
    _storage_prefix: str | None = None
    extra_metadata: dict[str, str] = Field(default_factory=dict)

    @property
    def storage_path(self) -> StoragePath:
        if self._storage_prefix is None:
            raise StoragePrefixIsNoneException(
                f"Cannot determine storage_path for {self.filename=}. "
                f"Storage prefix is None."
            )
        elif self.filename is None:
            raise FilenameIsNoneException(
                f"Cannot determine storage_path for file in {self._storage_prefix=}. "
                f"Filename is None."
            )
        return Path.join_path(self._storage_prefix, self.filename)

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
                raise MediaTypeCannotBeGuessedException(filename=filename)
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

    def __lt__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented

        return self.filename < other.filename

import base64

from pydantic import (
Field,
field_serializer,
field_validator,
)

from fennflow.files.media.base import BaseContent

class BinaryContent(BaseContent):
"""Base class for binary content type."""

    data: bytes = Field(repr=False)

    @property
    def data_size_mb(self) -> float:
        size_bytes = len(self.data)
        size_mb = round(size_bytes / (1024 * 1024), 2)
        return size_mb

    @field_serializer("data")
    def ser_data(self, v: bytes, _info):
        return base64.b64encode(v).decode("ascii")

    @field_validator("data", mode="before")
    @classmethod
    def de_data(cls, v):
        if isinstance(v, str):
            return base64.b64decode(v)
        return v

from .binary_content import BinaryContent

class AudioContent(BinaryContent):
"""Media content representing an audio file.

    Attributes:
        duration: Duration of the audio in seconds, if known.
    """

    duration: int | None = None

from .binary_content import BinaryContent

class ImageContent(BinaryContent):
"""Media content representing an image file.

    Attributes:
        height: Height of the image in pixels, if known.
        width: Width of the image in pixels, if known.
    """

    height: int | None = None
    width: int | None = None

from __future__ import annotations

import json
from typing import Generic, TypeVar

from pydantic import JsonValue

from ..._sentinel import OMIT, Omittable, is_given
from .abstract.content import ContentPropertyAbstract
from .abstract.from_content import FromContentAbstract
from .binary_content import BinaryContent

Value = TypeVar("Value", bound=JsonValue)

class JsonContent(
BinaryContent,
FromContentAbstract,
ContentPropertyAbstract,
Generic[Value],
):
"""Media content representing a JSON file.

    Stores JSON data as UTF-8 encoded bytes internally.
    Use ``from_content()`` to create from a Python object.

    Attributes:
        encoding: The text encoding. Defaults to ``"utf-8"``.

    Example::

        file = JsonContent.from_content({"key": "value"})
        print(file.content) # {"key": "value"}
        await uow.user_files.at("user1/").put(file)
    """

    encoding: str = "utf-8"

    @property
    def content(self) -> Value:
        text = self.data.decode(self.encoding)
        return json.loads(text)

    @classmethod
    def from_content(
        cls,
        data: Value,
        media_type: str = "application/json",
        encoding: str = "utf-8",
        filename: Omittable[str] = OMIT,
        ensure_ascii: bool = False,
        indent: int | str | None = None,
        **extra_json_dumps_kwargs,
    ) -> JsonContent[Value]:
        dumped_data = json.dumps(
            data,
            ensure_ascii=ensure_ascii,
            indent=indent,
            **extra_json_dumps_kwargs,
        )

        extra = {}
        if is_given(filename):
            extra["filename"] = filename

        return cls(
            data=dumped_data.encode(encoding),
            media_type=media_type,
            encoding=encoding,
            **extra,
        )

from .binary_content import BinaryContent

class DocumentContent(BinaryContent):
"""Media content representing a document."""
from __future__ import annotations

from typing import TYPE_CHECKING

from ..._sentinel import OMIT, Omittable, is_given
from .abstract.content import ContentPropertyAbstract
from .abstract.from_content import FromContentAbstract
from .binary_content import BinaryContent

if TYPE_CHECKING:
from typing_extensions import Self

class TextContent(
BinaryContent,
FromContentAbstract,
ContentPropertyAbstract,
):
"""Media content representing a plain text file.

    Stores text as UTF-8 encoded bytes internally.
    Use ``from_content()`` to create from a string.

    Attributes:
        encoding: The text encoding. Defaults to ``"utf-8"``.

    Example::

        file = TextContent.from_content("Hello, World!")
        print(file.content) # "Hello, World!"
        await uow.user_files.at("user1/").put(file)
    """

    encoding: str = "utf-8"

    @property
    def content(self) -> str:
        try:
            return self.data.decode(self.encoding)
        except UnicodeDecodeError as e:
            raise ValueError(f"Cannot extract text from {self=}") from e

    @classmethod
    def from_content(
        cls,
        data: str,
        media_type: str = "text/plain",
        encoding: str = "utf-8",
        filename: Omittable[str] = OMIT,
        **kwargs,  # noqa: ARG003
    ) -> Self:
        extra = {}

        if is_given(filename):
            extra["filename"] = filename

        return cls(
            data=data.encode(encoding),
            media_type=media_type,
            encoding=encoding,
            **extra,
        )

from .base import BaseContent

class UrlContent(BaseContent):
"""Media content representing a URL.

    Attributes:
        data: The URL string.
    """

    data: str

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

from __future__ import annotations

from functools import cache
from typing import TYPE_CHECKING, Any

from pydantic import ValidationError

from fennflow.files.media.binary_content import BinaryContent
from fennflow.files.media.url_content import UrlContent
from fennflow.files.registry import content_registry

if TYPE_CHECKING:
from fennflow.files.types import BinaryMedia

class ContentFactory:
"""Factory for creating media content instances from raw data.

    Resolves the appropriate content class from the registry based on
    MIME type, falling back to ``BinaryContent`` for unknown types.

    Example:
        content = ContentFactory.from_bytes("text/plain", b"Hello, World!")
        url = ContentFactory.from_url("https://example.com/file.txt")
    """

    @staticmethod
    @cache
    def _get_prefixes() -> list[str]:
        """Return registry prefixes sorted by length descending for match resolution."""
        return sorted(
            (p for p in content_registry if p.endswith("/")),
            key=len,
            reverse=True,
        )

    @classmethod
    def from_bytes(
        cls,
        media_type: str,
        data: bytes,
        **kwargs: Any,
    ) -> BinaryMedia:
        """Create a media content instance from raw bytes.

        Resolves the content class from the registry by exact MIME type match,
        then by prefix match, falling back to ``BinaryContent`` if no match is found.

        Args:
            media_type: The MIME type of the content (e.g. ``"text/plain"``).
            data: The raw bytes to wrap.
            **kwargs: Additional fields passed to the content model.

        Returns:
            A media content instance appropriate for the given MIME type.

        Raises:
            TypeError: If ``data`` is not bytes.
            ValueError: If the resolved content class fails validation.
        """
        if not isinstance(data, bytes):
            raise TypeError(f"Factory expected bytes, got {type(data)=} instead.")

        payload = {
            "media_type": media_type,
            "data": data,
            **kwargs,
        }

        if media_type in content_registry:
            content_cls = content_registry[media_type]
        else:
            for prefix in cls._get_prefixes():
                if media_type.startswith(prefix):
                    content_cls = content_registry[prefix]
                    break
            else:
                content_cls = BinaryContent

        try:
            return content_cls.model_validate(payload)
        except ValidationError as exc:
            raise ValueError(
                f"Failed to validate {content_cls.__name__=} for {media_type=}"
            ) from exc

    @staticmethod
    def from_url(
        url: str,
        media_type: str = "application/octet-stream",
        **kwargs: Any,
    ) -> UrlContent:
        """Create a ``UrlContent`` instance from a URL string.

        Args:
            url: The URL string to wrap.
            media_type: The MIME type of the resource.
                Defaults to ``"application/octet-stream"``.
            **kwargs: Additional fields passed to the content model.

        Returns:
            A ``UrlContent`` instance wrapping the given URL.

        Raises:
            ValueError: If the URL fails validation.
        """
        payload = {
            "data": url,
            "media_type": media_type,
            **kwargs,
        }
        try:
            return UrlContent.model_validate(payload)
        except ValidationError as exc:
            raise ValueError(f"Failed to create UrlContent for {url=}") from exc

3.

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from fennflow._sentinel import OMIT, Omittable

if TYPE_CHECKING:
from collections.abc import Iterable
from uuid import UUID

    from fennflow._new_types import StoragePath
    from fennflow._operations.dto import OperationRecord
    from fennflow.backends.abstract.config import AbstractBackendConfig
    from fennflow.backends.enums import OnConflictDoEnum
    from fennflow.backends.responses import OperationPage

class AbstractBackend(ABC):
"""Base class for all backends."""

    def __init__(self, config: AbstractBackendConfig) -> None:
        self._config = config
        self._operations: dict[StoragePath, OperationRecord] = {}

    @abstractmethod
    async def open(self) -> None: ...

    @abstractmethod
    async def close(self) -> None: ...

    @abstractmethod
    async def get(
        self,
        storage_path: StoragePath,
    ) -> OperationRecord | None: ...

    @abstractmethod
    async def add(self, record: OperationRecord) -> None: ...

    @abstractmethod
    async def exists(
        self,
        storage_path: StoragePath,
    ) -> bool: ...

    @abstractmethod
    async def list_pending(
        self,
    ) -> list[OperationRecord]: ...

    @abstractmethod
    async def mark_done(self, operation: OperationRecord) -> None: ...

    @abstractmethod
    async def mark_failed(
        self,
        operation: OperationRecord,
        error: str | None = None,
    ): ...

    @abstractmethod
    async def mark_compensation_failed(
        self,
        operation: OperationRecord,
        error: str | None = None,
    ): ...

    @abstractmethod
    async def clear_session(self) -> None: ...

    @abstractmethod
    async def flush(self): ...

    @abstractmethod
    async def rollback(self): ...

    @abstractmethod
    async def get_visible(
        self,
        prefix: str,
        limit: int,
        session_id: UUID,
        continuation_token: Omittable[str] = OMIT,
    ) -> OperationPage: ...

    @abstractmethod
    async def insert(
        self,
        operations: Iterable[OperationRecord],
        on_conflict: OnConflictDoEnum,
    ) -> None: ...

    @abstractmethod
    async def is_empty(self) -> bool: ...

from pydantic import BaseModel, Field

from fennflow._new_types import BackendScope

class AbstractBackendConfig(BaseModel):
"""Base configuration for all FennFlow backends."""

    scope: BackendScope = Field(
        default="fennflow_backend",
        description="Label to isolate backend state. "
        "Useful when working with multiple storage instances "
        "(e.g. two S3 or S3 and MinIO) "
        "to avoid merging their files' metadata.",
    )

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from typing_extensions import Unpack

from fennflow._operations.enums import OperationStatusEnum, OperationTypeEnum
from fennflow._sentinel import OMIT, Omittable
from fennflow.backends.abstract.base import AbstractBackend
from fennflow.backends.enums import OnConflictDoEnum
from fennflow.backends.exceptions import RecordAlreadyExistsException
from fennflow.backends.in_memory._select import SelectOperation

if TYPE_CHECKING:
from collections.abc import Iterable
from uuid import UUID

    from fennflow._new_types import BackendScope, StoragePath
    from fennflow._operations.dto import OperationRecord
    from fennflow.backends.abstract.annotations import SelectParams
    from fennflow.backends.in_memory import InMemoryBackendConfig
    from fennflow.backends.responses import OperationPage

class InMemoryBackend(AbstractBackend):
"""In-memory backend for managing file operations within a Unit of Work."""

    _storage: defaultdict[BackendScope, dict[StoragePath, OperationRecord]] | None = (
        None
    )

    def __init__(
        self,
        config: InMemoryBackendConfig,
    ):
        super().__init__(config=config)
        if self.__class__._storage is None:
            self.__class__._storage = defaultdict(dict)

    @property
    def storage(
        self,
    ) -> defaultdict[BackendScope, dict[StoragePath, OperationRecord]]:
        if self.__class__._storage is None:
            raise RuntimeError(
                "Cannot get in-memory storage. InMemoryBackend is not initialized.",
            )
        return self.__class__._storage

    @property
    def scoped_storage(self) -> dict[StoragePath, OperationRecord]:
        return self.storage[self._config.scope]

    async def open(
        self,
    ) -> None:
        pass

    async def close(
        self,
    ) -> None:
        await self.clear_session()

    async def add(
        self,
        record: OperationRecord,
    ) -> None:
        self._operations[record.storage_path] = record

    async def exists(
        self,
        storage_path: StoragePath,
    ) -> bool:
        return storage_path in self.storage[self._config.scope]

    async def get_from_storage(
        self,
        storage_path: StoragePath,
    ) -> OperationRecord | None:
        return self.storage[self._config.scope].get(storage_path)

    async def get(
        self,
        storage_path: StoragePath,
    ) -> OperationRecord | None:
        return self._operations.get(storage_path) or self.storage[
            self._config.scope
        ].get(storage_path)

    async def list_pending(
        self,
    ) -> list[OperationRecord]:
        return [
            operation for operation in self._operations.values() if operation.is_pending
        ]

    async def mark_done(
        self,
        operation: OperationRecord,
    ) -> None:
        if operation.operation_type == OperationTypeEnum.PUT:
            operation.status = OperationStatusEnum.UPLOADED
        elif operation.operation_type == OperationTypeEnum.DELETE:
            operation.status = OperationStatusEnum.DELETED
        else:
            raise NotImplementedError(
                f"mark_done is not supported for {operation.operation_type=}"
            )

    async def mark_failed(
        self,
        operation: OperationRecord,
        error: str | None = None,
    ) -> None:
        operation.status = OperationStatusEnum.FAILED
        operation.error = error

    async def mark_compensation_failed(
        self,
        operation: OperationRecord,
        error: str | None = None,
    ):
        operation.status = OperationStatusEnum.COMPENSATION_FAILED
        operation.error = error

    async def mark_pending(
        self,
        operation: OperationRecord,
    ) -> None:
        operation.status = OperationStatusEnum.PENDING

    async def clear_session(
        self,
    ) -> None:
        self._operations.clear()

    async def flush(
        self,
    ):
        for key, operation in self._operations.items():
            storage_operation = await self.get_from_storage(
                storage_path=operation.storage_path,
            )

            if storage_operation and storage_operation.is_locked(
                current_session_id=operation.session_id
            ):
                raise RecordAlreadyExistsException(
                    f"{operation.storage_path=} already exists"
                )
            self.storage[self._config.scope][key] = operation

    async def rollback(
        self,
        error: str | None = None,
    ) -> None:
        for operation in self._operations.values():
            await self.mark_failed(
                operation=operation,
                error=error,
            )

    @classmethod
    def drop_all(cls) -> None:
        cls._storage = defaultdict(dict)

    async def select(
        self,
        **kwargs: Unpack[SelectParams],
    ) -> OperationPage:
        select = SelectOperation(**kwargs)

        return select.select(record=(record for record in self.scoped_storage.values()))

    async def get_visible(
        self,
        prefix: str,
        limit: int,
        session_id: UUID,
        continuation_token: Omittable[str] = OMIT,
    ) -> OperationPage:
        return await self.select(
            prefix=prefix,
            continuation_token=continuation_token,
            limit=limit,
            visible_for_session_id=session_id,
        )

    async def is_empty(self) -> bool:
        return not bool(self.scoped_storage)

    async def insert(
        self,
        operations: Iterable[OperationRecord],
        on_conflict: OnConflictDoEnum,
    ) -> None:
        for operation in operations:
            op_in_storage = self.scoped_storage.get(operation.storage_path)

            if op_in_storage:
                match on_conflict:
                    case OnConflictDoEnum.DO_NOTHING:
                        continue
                    case OnConflictDoEnum.REPLACE:
                        self.scoped_storage[operation.storage_path] = operation
                    case OnConflictDoEnum.RAISE:
                        raise ValueError(
                            f"There is already record with {operation.storage_path=}"
                        )
                    case _:
                        raise AssertionError("Unhandled conflict strategy.")
            else:
                self.scoped_storage[operation.storage_path] = operation

from fennflow.backends.abstract.config import AbstractBackendConfig

class InMemoryBackendConfig(AbstractBackendConfig):
"""Configuration for the in-memory backend.

    No configuration is required — the in-memory backend
    is zero-dependency.
    """

from __future__ import annotations

from typing import TYPE_CHECKING

from .registry import backend_registry

if TYPE_CHECKING:
from fennflow.backends.abstract.base import AbstractBackend
from fennflow.backends.types.config import BackendConfig

class BackendFactory:
"""Factory for creating backends from config."""

    @staticmethod
    def from_config(config: BackendConfig) -> AbstractBackend:

        backend_cls = backend_registry.get(config.__class__.__name__)
        if not backend_cls:
            raise ValueError(f"Unknown backend for : {type(config)=}")

        return backend_cls(config=config)

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from fennflow._sentinel import OMIT, Omittable
from fennflow.repositories.fields.base import RepoExtra

if TYPE_CHECKING:
from typing_extensions import Self

    from fennflow._new_types import Namespace, StoragePath
    from fennflow.files.responses.base import MediaResponse
    from fennflow.files.responses.list import ListResponse
    from fennflow.files.types import BinaryMedia

RepoExtraType = TypeVar("RepoExtraType", bound=RepoExtra)

class AbstractConnector(ABC, Generic[RepoExtraType]):
"""Base class for all FennFlow storage connectors.

    A connector is responsible for performing actual file operations
    against a storage backend (e.g. S3, local filesystem, in-memory).
    All operations are async and integrate with the Saga execution flow
    via ``OperationExecutor``.

    To implement a custom connector, subclass this and implement all
    abstract methods. Register it in ``connector_registry`` to make it
    available via ``ConnectorFactory``.
    """

    @abstractmethod
    async def open(self) -> Self:
        """Initialize the connector and return self."""

    @abstractmethod
    async def close(self) -> Any:
        """Clean up resources."""

    @abstractmethod
    async def put(
        self,
        file: BinaryMedia,
        repo_extra: RepoExtraType,
        **extra: dict[Any, Any],
    ) -> Any:
        """Upload a file to storage."""

    @abstractmethod
    async def get(
        self,
        storage_path: StoragePath,
        repo_extra: RepoExtraType,
        **extra: dict[Any, Any],
    ) -> MediaResponse:
        """Download a file from storage."""

    @abstractmethod
    async def delete(
        self,
        storage_path: StoragePath,
        repo_extra: RepoExtraType,
        **extra: dict[Any, Any],
    ):
        """Delete a file from storage."""

    @abstractmethod
    async def copy_object(
        self,
        repo_extra: RepoExtraType,
        from_storage_path: StoragePath,
        to_storage_path: StoragePath,
        to_namespace: Namespace,
        **extra: dict[Any, Any],
    ):
        """Copy a file within or across namespaces."""

    @abstractmethod
    async def list_objects(
        self,
        prefix: str,
        repo_extra: RepoExtraType,
        limit: int = 1000,
        continuation_token: Omittable[str] | None = OMIT,
        **extra: dict[Any, Any],
    ) -> ListResponse:
        """List all files in storage."""

from pydantic import BaseModel

class InMemoryConnectorConfig(BaseModel):
"""Configuration for the in-memory connector.

    No configuration is required — the in-memory connector
    is zero-dependency and is intended for testing and development only.
    """

from __future__ import annotations

import bisect
import logging
from collections import defaultdict
from itertools import islice
from typing import TYPE_CHECKING, Any

from fennflow._sentinel import OMIT, Omittable
from fennflow.connectors.abstract import AbstractConnector
from fennflow.files import ContentFactory
from fennflow.files.responses.base import MediaResponse
from fennflow.files.responses.list import ListResponse

if TYPE_CHECKING:
from typing_extensions import Self

    from fennflow._new_types import Namespace, StoragePath
    from fennflow.connectors.abstract.base import RepoExtraType
    from fennflow.connectors.in_memory.config import InMemoryConnectorConfig
    from fennflow.files.types import BinaryMedia
    from fennflow.repositories.fields.base import RepoExtra

logger = logging.getLogger(__name__)

class InMemoryConnector(AbstractConnector):
"""In-memory connector for file storage, primarily used for testing.

    Stores files in a class-level dictionary shared across all instances,

    Use ``drop_all()`` between tests to reset state.

    Example::

        class UOW(UnitOfWork):
            config = ConfigDict(
                connector=InMemoryConnectorConfig(),
            )
    """

    _storage: defaultdict[Namespace, dict[StoragePath, BinaryMedia]] | None = None

    async def open(self) -> Self:
        return self

    async def close(self):
        pass

    def __init__(self, config: InMemoryConnectorConfig):
        self._config = config

        if self.__class__._storage is None:
            self.__class__._storage = defaultdict(dict)

    @property
    def storage(
        self,
    ) -> defaultdict[Namespace, dict[StoragePath, BinaryMedia]]:
        if self.__class__._storage is None:
            raise RuntimeError(
                "Cannot get in-memory storage. InMemoryConnector is not initialized.",
            )
        return self.__class__._storage

    async def put(
        self,
        file: BinaryMedia,
        repo_extra: RepoExtra,
        **extra,  # noqa: ARG002
    ) -> None:
        namespace = repo_extra["namespace"]
        self.storage[namespace][file.storage_path] = file
        logger.debug(f"{file=} uploaded to {namespace=}")

    async def get(
        self,
        storage_path: StoragePath,
        repo_extra: RepoExtra,
        **extra: dict[Any, Any],  # noqa: ARG002
    ) -> MediaResponse:

        if storage_path not in self.storage[repo_extra["namespace"]]:
            return MediaResponse()

        file = self.storage[repo_extra["namespace"]][storage_path]

        return MediaResponse(
            media=(
                ContentFactory.from_bytes(
                    media_type=file.media_type,
                    data=file.data,
                    **file.get_metadata(),
                ),
            )
        )

    async def delete(
        self,
        storage_path: StoragePath,
        repo_extra: RepoExtra,
        **extra: dict[Any, Any],  # noqa: ARG002
    ):
        self.storage[repo_extra["namespace"]].pop(storage_path, None)

    async def copy_object(
        self,
        repo_extra: RepoExtra,
        from_storage_path: StoragePath,
        to_storage_path: StoragePath,
        to_namespace: Namespace,
        **extra: dict[Any, Any],  # noqa: ARG002
    ):
        file = self.storage[repo_extra["namespace"]].get(from_storage_path)
        if file:
            self.storage[to_namespace][to_storage_path] = file

    @classmethod
    def drop_all(cls) -> None:
        cls._storage = defaultdict(dict)

    async def list_objects(
        self,
        prefix: str,
        repo_extra: RepoExtraType,
        limit: int = 1000,
        continuation_token: Omittable[str] | None = OMIT,
        **extra: dict[Any, Any],  # noqa: ARG002
    ) -> ListResponse:
        filtered_storage_paths = []
        all_storage_paths = sorted(self.storage[repo_extra["namespace"]])

        if continuation_token:
            index = bisect.bisect_right(all_storage_paths, continuation_token)
        else:
            index = 0

        for storage_path in islice(all_storage_paths, index, None):
            if 0 >= limit:
                continuation_token = storage_path
                break

            if storage_path.startswith(prefix):
                filtered_storage_paths.append(storage_path)
                limit -= 1
        else:
            continuation_token = None

        return ListResponse(
            storage_paths=filtered_storage_paths,
            continuation_token=continuation_token,
        )

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
from aiobotocore.session import AioSession, ClientCreatorContext
from types_aiobotocore_s3 import S3Client as S3ClientAiobotocore
from typing_extensions import Self

    from fennflow.connectors.s3 import S3ConnectorConfig

logger = logging.getLogger(__name__)

class S3Client:
"""Async S3 client wrapper around aiobotocore.

    Manages the lifecycle of an aiobotocore client context.
    Use ``open()`` and ``close()`` to manage the connection,
    or use it as an async context manager.

    Args:
        session: The aiobotocore session to create the client from.
        config: Optional S3 connector configuration. If not provided,
            the AWS credential chain is used.

    Example::

        s3_client = await S3Client(session=session, config=config).open()
        await s3_client.client.put_object(...)
        await s3_client.close()
    """

    def __init__(
        self,
        session: AioSession,
        config: S3ConnectorConfig | None = None,
    ):
        self.config: S3ConnectorConfig | None = config
        self.session = session
        self._client: S3ClientAiobotocore | None = None
        self._context: ClientCreatorContext | None = None

    async def open(self) -> Self:
        _context = self.session.create_client("s3", **self.session_kwargs)
        self._client = await _context.__aenter__()
        self._context = _context
        return self

    async def close(self) -> bool:
        if self._context:
            await self._context.__aexit__(None, None, None)
            self._client = None
            self._context = None
            return True
        return False

    @property
    def client(self) -> S3ClientAiobotocore:
        if not self._client:
            raise RuntimeError("S3 client is not initialized. Call init() first.")
        return self._client

    @property
    def session_kwargs(self) -> dict:
        if self.config is None:
            return {}

        return {
            "aws_access_key_id": self.config.aws_access_key_id,
            "aws_secret_access_key": self.config.aws_secret_access_key,
            "endpoint_url": self.config.endpoint_url,
            "config": self.config.aiobotocore_config,
        }

from aiobotocore.config import AioConfig
from pydantic import BaseModel, ConfigDict

class S3ConnectorConfig(BaseModel):
"""Configuration for the S3 connector.

    Credentials can be provided explicitly via this config or through any method
    supported by the AWS credential chain
    (environment variables, ``~/.aws/credentials``, IAM roles, etc.).
    See the `AWS documentation
    <https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html>`_
    for the full list of supported options.

    Attributes:
        aws_access_key_id: AWS access key ID.
        aws_secret_access_key: AWS secret access key.
        endpoint_url: Custom endpoint URL for S3-compatible storage.
        aiobotocore_config: Advanced aiobotocore client configuration.

    Example::

        # explicit credentials
        class UOW(UnitOfWork):
            user_files = UserFiles
            config = ConfigDict(
                        connector=S3ConnectorConfig(
                                aws_access_key_id="key",
                                aws_secret_access_key="secret",
                                )
                                )


        # rely on AWS credential chain
        S3ConnectorConfig()
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    endpoint_url: str | None = None
    aiobotocore_config: AioConfig | None = None

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from aiobotocore.session import get_session

from fennflow._sentinel import OMIT, Omittable
from fennflow.connectors.abstract import AbstractConnector
from fennflow.connectors.s3.client import S3Client
from fennflow.files import ContentFactory
from fennflow.files.responses.base import MediaResponse
from fennflow.files.responses.list import ListResponse
from fennflow.repositories.fields.s3 import S3Extra

if TYPE_CHECKING:
from aiobotocore.session import AioSession
from typing_extensions import Self

    from fennflow._new_types import Namespace, StoragePath
    from fennflow.connectors.abstract.base import RepoExtraType
    from fennflow.connectors.s3 import S3ConnectorConfig
    from fennflow.files.types import BinaryMedia

logger = logging.getLogger(__name__)

class S3Connector(AbstractConnector[S3Extra]):
"""Connector for AWS S3-compatible object storage via aiobotocore.

    Use ``S3ConnectorConfig`` to configure credentials, region, etc.

    Example::

        class UOW(UnitOfWork):
            config = ConfigDict(
                connector=S3ConnectorConfig(...),
            )
    """

    _aio_session: AioSession | None = None

    def __init__(
        self,
        config: S3ConnectorConfig,
    ):
        self._config = config
        self._client: S3Client | None = None

    @property
    def aio_session(self) -> AioSession:
        if self.__class__._aio_session is None:
            raise RuntimeError("AioSession is not initialized.")

        return self.__class__._aio_session

    async def open(
        self,
    ) -> Self:
        if self.__class__._aio_session is None:
            self.__class__._aio_session = get_session()

        self._client = await S3Client(
            config=self._config,
            session=self.aio_session,
        ).open()
        return self

    async def close(
        self,
    ):
        if self._client:
            await self._client.close()
            self._client = None

    @property
    def s3client(
        self,
    ) -> S3Client:
        if self._client is None:
            raise RuntimeError("S3Connector client is not initialized.")
        return self._client

    async def put(
        self,
        file: BinaryMedia,
        repo_extra: S3Extra,
        **sdk_extra: Any,
    ) -> None:
        bucket_name = repo_extra["namespace"]
        await self.s3client.client.put_object(
            Bucket=bucket_name,
            Key=file.storage_path,
            Body=file.data,
            ContentType=file.media_type,
            Metadata=file.get_metadata(),
            **sdk_extra,
        )
        logger.debug(f"{file=} uploaded to {bucket_name=}")

    async def get(
        self,
        storage_path: StoragePath,
        repo_extra: S3Extra,
        **sdk_extra: Any,
    ) -> MediaResponse:
        response = await self.s3client.client.get_object(
            Bucket=repo_extra["namespace"],
            Key=storage_path,
            **sdk_extra,
        )
        if not response:
            return MediaResponse()

        return MediaResponse(
            media=(
                ContentFactory.from_bytes(
                    media_type=response["ContentType"],
                    data=await response["Body"].read(),
                    **response.get("Metadata", {}),
                ),
            ),
        )

    async def delete(
        self,
        storage_path: StoragePath,
        repo_extra: S3Extra,
        **sdk_extra: Any,
    ):
        bucket_name = repo_extra["namespace"]
        await self.s3client.client.delete_object(
            Bucket=bucket_name,
            Key=storage_path,
            **sdk_extra,
        )
        logger.debug(f"file with {storage_path=} deleted from {bucket_name=}")

    async def copy_object(
        self,
        repo_extra: S3Extra,
        from_storage_path: StoragePath,
        to_storage_path: StoragePath,
        to_namespace: Namespace,
        **sdk_extra: Any,
    ):
        bucket_name = repo_extra["namespace"]

        await self.s3client.client.copy_object(
            CopySource={"Bucket": bucket_name, "Key": from_storage_path},
            Bucket=to_namespace,
            Key=to_storage_path,
            **sdk_extra,
        )
        logger.debug(
            f"file from {bucket_name=} with {from_storage_path=} "
            f"copied to {to_namespace=}"
        )

    async def list_objects(
        self,
        prefix: str,
        repo_extra: RepoExtraType,
        limit: int = 1000,
        continuation_token: Omittable[str] | None = OMIT,
        **extra: Any,
    ) -> ListResponse:

        if continuation_token:
            extra["ContinuationToken"] = continuation_token

        response = await self.s3client.client.list_objects_v2(
            Bucket=repo_extra["namespace"],
            Prefix=prefix,
            MaxKeys=limit,
            **extra,
        )

        return ListResponse(
            storage_paths=tuple(obj["Key"] for obj in response.get("Contents", [])),
            continuation_token=response.get("NextContinuationToken"),
        )

from __future__ import annotations

from typing import TYPE_CHECKING

from .registry import connector_registry

if TYPE_CHECKING:
from .abstract import AbstractConnector
from .types.config import ConnectorConfig

class ConnectorFactory:
"""Factory for creating connector instances from config objects.

    Resolves the appropriate connector class from ``connector_registry``
    based on the config class name.

    Example::

        connector = ConnectorFactory.from_config(S3ConnectorConfig(...))
    """

    @staticmethod
    def from_config(config: ConnectorConfig) -> AbstractConnector:
        """Create a connector instance from a config object.

        Args:
            config: The connector configuration instance.

        Returns:
            An initialized connector instance.

        Raises:
            ValueError: If no connector is registered for the config type.
        """
        connector_cls = connector_registry.get(config.__class__.__name__)
        if not connector_cls:
            raise ValueError(f"Unknown connector for : {type(config)=}")

        return connector_cls(config=config)

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from fennflow._decorators import reraise_with
from fennflow._operations.dto import OperationRecord
from fennflow._operations.enums import OperationStatusEnum, OperationTypeEnum
from fennflow._reconciler.enums import ReconcileStrategyEnum
from fennflow._reconciler.exceptions import ReconcileFailedException
from fennflow.backends.enums import OnConflictDoEnum
from fennflow.repositories import RepoField

if TYPE_CHECKING:
from collections.abc import AsyncGenerator, Generator, Iterable
from uuid import UUID

    from fennflow import UnitOfWork
    from fennflow.backends.abstract.base import AbstractBackend
    from fennflow.connectors.abstract import AbstractConnector
    from fennflow.files.responses.list import ListResponse
    from fennflow.repositories.fields.base import RepoExtra

logger = logging.getLogger(__name__)

reconcile_to_on_conflict_strategy = {
ReconcileStrategyEnum.REPLACE: OnConflictDoEnum.REPLACE,
ReconcileStrategyEnum.INSERT_MISSING: OnConflictDoEnum.DO_NOTHING,
ReconcileStrategyEnum.FILL_IF_EMPTY: OnConflictDoEnum.RAISE,
}

class Reconciler:
def __init__(
self,
uow_fields: Iterable[RepoField],
backend: AbstractBackend,
connector: AbstractConnector,
) -> None:
self.uow_fields = uow_fields
self.backend = backend
self.connector = connector

    @reraise_with(ReconcileFailedException())
    async def reconcile(
        self,
        session_id: UUID,
        strategy: ReconcileStrategyEnum,
        batch_size: int,
    ) -> None:
        for repo in self.uow_fields:
            if not await self._should_reconcile(strategy=strategy):
                continue

            on_conflict = reconcile_to_on_conflict_strategy[strategy]

            async for page in self._iter_pages(repo, batch_size=batch_size):
                await self.backend.insert(
                    operations=self._records_from_page(
                        session_id=session_id,
                        page=page,
                        repo_extra=repo.repo_extra,
                    ),
                    on_conflict=on_conflict,
                )

    async def _should_reconcile(self, strategy: ReconcileStrategyEnum) -> bool:
        if strategy == ReconcileStrategyEnum.FILL_IF_EMPTY:
            return await self.backend.is_empty()
        return True

    async def _iter_pages(
        self,
        repo: RepoField,
        batch_size: int,
    ) -> AsyncGenerator[ListResponse, None]:
        continuation_token = None

        while True:
            page = await self.connector.list_objects(
                prefix="",
                limit=batch_size,
                repo_extra=repo.repo_extra,
                continuation_token=continuation_token,
            )
            yield page

            if page.continuation_token is None:
                break
            continuation_token = page.continuation_token

    @staticmethod
    def _records_from_page(
        session_id: UUID,
        page: ListResponse,
        repo_extra: RepoExtra,
    ) -> Generator[OperationRecord, None, None]:
        for storage_path in page:
            yield OperationRecord(
                session_id=session_id,
                storage_path=storage_path,
                operation_type=OperationTypeEnum.PUT,
                status=OperationStatusEnum.UPLOADED,
                repo_extra=repo_extra,
            )

    @staticmethod
    def _get_repo_fields(uow: UnitOfWork) -> Generator[RepoField, None, None]:
        for field in vars(type(uow)).values():
            if isinstance(field, RepoField):
                yield field

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, ClassVar

from fennflow._reconciler.core import Reconciler
from fennflow._reconciler.enums import ReconcileFrequencyEnum
from fennflow.uow.inspector import UowInspector

if TYPE_CHECKING:
from fennflow import UnitOfWork
from fennflow._new_types import UowQualName

logger = logging.getLogger(__name__)

class ReconcileOrchestrator:
_reconciled_on_startup: ClassVar[set[UowQualName]] = set()
_lock: asyncio.Lock = asyncio.Lock()

    async def reconcile_if_needed(self, uow: UnitOfWork) -> None:
        frequency = uow._resolved_config.reconcile.frequency

        async with self._lock:
            match frequency:
                case ReconcileFrequencyEnum.NEVER:
                    await self._handle_never(uow=uow)
                case ReconcileFrequencyEnum.ON_START_APP:
                    await self._handle_on_start_app(uow=uow)
                case ReconcileFrequencyEnum.ON_SESSION_START:
                    await self._handle_on_session_start(uow=uow)
                case _:
                    raise AssertionError("Unhandled frequency")

    async def _handle_never(self, uow: UnitOfWork) -> None:
        logger.debug(
            "Skipping reconciliation.",
            extra=self._log_extra(uow),
        )

    async def _handle_on_start_app(self, uow: UnitOfWork) -> None:
        if uow.__class__.__qualname__ in self._reconciled_on_startup:
            logger.debug(
                "Skipping reconciliation.",
                extra=self._log_extra(uow=uow),
            )
            return

        logger.debug(
            "Starting reconciliation...",
            extra=self._log_extra(uow=uow),
        )
        await self._reconcile(uow=uow)
        self._reconciled_on_startup.add(uow.__class__.__qualname__)

    async def _handle_on_session_start(self, uow: UnitOfWork) -> None:
        logger.debug("Starting reconciliation...", extra=self._log_extra(uow=uow))
        await self._reconcile(uow=uow)

    async def _reconcile(self, uow: UnitOfWork) -> None:
        extractor = UowInspector(uow=uow)
        reconcile = Reconciler(
            uow_fields=extractor.get_repo_fields(),
            connector=uow.connector,
            backend=uow.backend,
        )

        await reconcile.reconcile(
            session_id=uow._session_id,
            batch_size=uow._resolved_config.reconcile.batch_size,
            strategy=uow._resolved_config.reconcile.strategy,
        )

        logger.debug(
            "Finished reconciliation.",
            extra=self._log_extra(uow=uow),
        )

    @staticmethod
    def _log_extra(uow: UnitOfWork) -> dict[str, Any]:
        return {
            "session_id": uow._session_id,
            "uow_class_name": uow.__class__.__qualname__,
            "frequency": uow._resolved_config.reconcile.frequency,
        }

from dataclasses import dataclass

from fennflow._reconciler.enums import ReconcileFrequencyEnum, ReconcileStrategyEnum

@dataclass(slots=True, frozen=True)
class ReconcileConfig:
frequency: ReconcileFrequencyEnum = ReconcileFrequencyEnum.ON_START_APP
strategy: ReconcileStrategyEnum = ReconcileStrategyEnum.FILL_IF_EMPTY
batch_size: int = 1000
from enum import IntEnum, auto

class ReconcileFrequencyEnum(IntEnum):
"""Controls how often reconciliation is performed.

    Attributes:
        ON_START_APP: Reconcile once per process lifetime.
        ON_SESSION_START: Reconcile on every ``UnitOfWork.__aenter__`` call.
        NEVER: Disable reconciliation.
    """

    ON_START_APP = auto()
    ON_SESSION_START = auto()
    NEVER = auto()

class ReconcileStrategyEnum(IntEnum):
"""Defines how reconciliation updates existing data.

    Attributes:
        FILL_IF_EMPTY: Reconcile only if the backend is empty.
        REPLACE: Reset all backend data before reconciling.
        INSERT_MISSING: Insert missing data while keeping existing data intact.
    """

    FILL_IF_EMPTY = auto()
    REPLACE = auto()
    INSERT_MISSING = auto()

6.

from __future__ import annotations

from typing import TYPE_CHECKING

from .registry import flow_registry

if TYPE_CHECKING:
from fennflow.connectors.abstract import AbstractConnector

    from .dto import OperationRecord

class OperationExecutor:
def __init__(self, connector: AbstractConnector) -> None:
self.connector = connector

    async def execute(
        self,
        operation: OperationRecord,
        **provider_extra,
    ):
        operation_flow = flow_registry[operation.operation_type]
        return await operation_flow().execute(
            operation=operation,
            connector=self.connector,
            **provider_extra,
        )

    async def compensate(
        self,
        operation: OperationRecord,
    ):
        operation_flow = flow_registry[operation.operation_type]
        return await operation_flow().compensate(
            operation=operation,
            connector=self.connector,
        )

    async def finalize(
        self,
        operation: OperationRecord,
    ):
        operation_flow = flow_registry[operation.operation_type]
        return await operation_flow().finalize(
            operation=operation,
            connector=self.connector,
        )

finalize (just clean up. Used as finally in try except finally)

from __future__ import annotations

import datetime
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from uuid import UUID

from fennflow._datetime import now
from fennflow._operations.context.abstract import BaseContext
from fennflow._operations.enums import OperationStatusEnum, OperationTypeEnum
from fennflow._sentinel import NOT_GIVEN

if TYPE_CHECKING:
from fennflow._new_types import Namespace, StoragePath
from fennflow._operations.context.types import Context
from fennflow._sentinel import NotGiven
from fennflow.repositories.fields.base import RepoExtra

@dataclass(slots=True)
class OperationRecord:
session_id: uuid.UUID
storage_path: StoragePath
repo_extra: RepoExtra
operation_type: OperationTypeEnum
status: OperationStatusEnum
context: Context = field(default_factory=BaseContext)
operation_id: uuid.UUID = field(default_factory=uuid.uuid4)

    created_at: datetime.datetime = field(
        default_factory=now,
    )
    expired_at: datetime.datetime = field(
        default_factory=lambda: now() + datetime.timedelta(seconds=30)
    )
    error: str | None | NotGiven = NOT_GIVEN

    @property
    def is_pending(self) -> bool:
        return self.status == OperationStatusEnum.PENDING

    @property
    def is_uploaded(self) -> bool:
        return self.status == OperationStatusEnum.UPLOADED

    @property
    def is_failed(self) -> bool:
        return self.status == OperationStatusEnum.FAILED

    @property
    def is_deleted(self) -> bool:
        return self.status == OperationStatusEnum.DELETED

    @property
    def namespace(self) -> Namespace:
        return self.repo_extra["namespace"]

    @property
    def is_expired(self):
        return self.expired_at < now()

    @property
    def is_dangling(self) -> bool:
        return self.is_expired and not self.is_uploaded

    def is_locked(self, current_session_id: UUID) -> bool:
        return (
            self.session_id != current_session_id
            and self.is_pending
            and not self.is_expired
        )

    def is_visible(self, requested_from_session_id: UUID) -> bool:
        return self.is_uploaded or (
            self.is_pending
            and self.session_id == requested_from_session_id
            and self.operation_type == OperationTypeEnum.PUT
        )

7.

from typing_extensions import TypedDict

from fennflow._reconciler import ReconcileConfig
from fennflow.backends.types.config import BackendConfig
from fennflow.connectors.types.config import ConnectorConfig

class ConfigDict(TypedDict, total=False):
"""Configuration for a UnitOfWork instance.

    All fields are optional — if not provided, defaults are used.

    Attributes:
        backend: Configuration for the metadata backend
            (e.g. ``InMemoryBackendConfig``).
        connector: Configuration for the storage connector (e.g. ``S3ConnectorConfig``).

    Example:
        class UOW(UnitOfWork):
            config = ConfigDict(
                backend=InMemoryBackendConfig(),
                connector=S3ConnectorConfig(...),
            )
    """

    backend: BackendConfig
    connector: ConnectorConfig
    reconcile: ReconcileConfig

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from fennflow._reconciler import (
ReconcileConfig,
ReconcileFrequencyEnum,
ReconcileStrategyEnum,
)
from fennflow.backends.in_memory import InMemoryBackendConfig
from fennflow.connectors import InMemoryConnectorConfig

if TYPE_CHECKING:
from fennflow import ConfigDict
from fennflow.backends.types.config import BackendConfig
from fennflow.connectors.types.config import ConnectorConfig

@dataclass(slots=True)
class ResolvedConfig:
backend: BackendConfig
connector: ConnectorConfig
reconcile: ReconcileConfig

class ConfigResolver:
@classmethod
def resolve_config(
cls,
config: ConfigDict | None,
) -> ResolvedConfig:
cfg = config or {}
backend_cfg = cfg.get("backend") or InMemoryBackendConfig()
reconcile_cfg = cfg.get("reconcile")

        if reconcile_cfg is None:
            reconcile_cfg = cls._get_default_reconcile_config(backend_cfg=backend_cfg)

        return ResolvedConfig(
            backend=backend_cfg,
            connector=cfg.get("connector") or InMemoryConnectorConfig(),
            reconcile=reconcile_cfg,
        )

    @staticmethod
    def _get_default_reconcile_config(backend_cfg: BackendConfig) -> ReconcileConfig:
        # InMemoryBackend loses state on restart —
        # reconcile on every app start by default.

        # Persistent backends (Postgres, Redis, etc.) default to NEVER
        # Since it needs reconciliation on first connection
        default_reconcile = (
            ReconcileConfig(
                frequency=ReconcileFrequencyEnum.ON_START_APP,
                strategy=ReconcileStrategyEnum.FILL_IF_EMPTY,
            )
            if isinstance(backend_cfg, InMemoryBackendConfig)
            else ReconcileConfig()
        )

        return default_reconcile

Roadmap table:
Title URL Assignees Status Linked pull requests Sub-issues progress
Implement "Sqlalchemy" backend    https://github.com/Alex-FIR-IT/FennFlow/issues/3    Alex-FIR-IT In Progress		
Publish FennFlow to PyPI    https://github.com/Alex-FIR-IT/FennFlow/issues/30    Alex-FIR-IT
Done    https://github.com/Alex-FIR-IT/FennFlow/pull/36
Implement a mechanism for synchronization between backend and file
storage.    https://github.com/Alex-FIR-IT/FennFlow/issues/22    Alex-FIR-IT Done		
Implement LocalConnector    https://github.com/Alex-FIR-IT/FennFlow/issues/19    Alex-FIR-IT Next up		
Implement GeneratePresignedURLRepository    https://github.com/Alex-FIR-IT/FennFlow/issues/8    Alex-FIR-IT Next up		
Implement UpsertRepository    https://github.com/Alex-FIR-IT/FennFlow/issues/21    Alex-FIR-IT Next up		
Add MediaType enum    https://github.com/Alex-FIR-IT/FennFlow/issues/33    Alex-FIR-IT Next up		
Implement NoOpBackend    https://github.com/Alex-FIR-IT/FennFlow/issues/15    Alex-FIR-IT Rejected		
Implement UnitOfWork    https://github.com/Alex-FIR-IT/FennFlow/issues/6    Alex-FIR-IT Done		
Implement AtRepository    https://github.com/Alex-FIR-IT/FennFlow/issues/13    Alex-FIR-IT Done		
Implement ListObjectsRepository    https://github.com/Alex-FIR-IT/FennFlow/issues/9    Alex-FIR-IT Done		
Create a few repositories for CRUD operations    https://github.com/Alex-FIR-IT/FennFlow/issues/7    Alex-FIR-IT Done
3 / 3 (100%)
Implement "in-memory" backend    https://github.com/Alex-FIR-IT/FennFlow/issues/1    Alex-FIR-IT Done		
Add classmethod from_filepath in BinaryContent    https://github.com/Alex-FIR-IT/FennFlow/issues/4    Alex-FIR-IT
Backlog		
Implement pydantic classes that represent media content    https://github.com/Alex-FIR-IT/FennFlow/issues/5
Alex-FIR-IT Done		
Implement InMemoryConnector for tests    https://github.com/Alex-FIR-IT/FennFlow/issues/17    Alex-FIR-IT Done		
Implement S3Connector    https://github.com/Alex-FIR-IT/FennFlow/issues/16    Alex-FIR-IT Done		
Annotate extra    https://github.com/Alex-FIR-IT/FennFlow/issues/18    Alex-FIR-IT Backlog		
Impelemnt ReplaceRepository    https://github.com/Alex-FIR-IT/FennFlow/issues/20    Alex-FIR-IT Backlog		
Implement "Redis" backend    https://github.com/Alex-FIR-IT/FennFlow/issues/2    Alex-FIR-IT Backlog		
Add Slim Distribution for FennFlow    https://github.com/Alex-FIR-IT/FennFlow/issues/27    Alex-FIR-IT ideas		
Add MyPy type checking to GitHub Actions CI    https://github.com/Alex-FIR-IT/FennFlow/issues/29    Alex-FIR-IT ideas		
Add CI testing matrix for Python 3.10–3.14    https://github.com/Alex-FIR-IT/FennFlow/issues/32    Alex-FIR-IT
Done    https://github.com/Alex-FIR-IT/FennFlow/pull/36
feat: change publishing settings for uploading to pypi instead of
testpypi    https://github.com/Alex-FIR-IT/FennFlow/pull/36    Alex-FIR-IT Done		