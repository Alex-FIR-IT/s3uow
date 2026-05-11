from __future__ import annotations

import bisect
import logging
from collections import defaultdict
from itertools import islice
from typing import TYPE_CHECKING, Any, Self

from fennflow._sentinel import OMIT, Omittable
from fennflow.connectors.abstract import AbstractConnector
from fennflow.files import ContentFactory
from fennflow.files.responses.base import MediaResponse
from fennflow.files.responses.list import ListResponse

if TYPE_CHECKING:
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
        logger.info(f"{file=} uploaded to {namespace=}")

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
