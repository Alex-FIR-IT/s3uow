from __future__ import annotations

import logging
from collections import defaultdict
from typing import TYPE_CHECKING, Any, Self

from fennflow.connectors.abstract import AbstractConnector
from fennflow.files import ContentFactory
from fennflow.files.responses.base import MediaResponse

if TYPE_CHECKING:
    from fennflow._new_types import Filepath, Namespace
    from fennflow.connectors.in_memory.config import InMemoryConnectorConfig
    from fennflow.files.types import BinaryMedia


logger = logging.getLogger(__name__)


class InMemoryConnector(AbstractConnector):
    _storage: defaultdict[Namespace, dict[Filepath, BinaryMedia]] | None = None

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
    ) -> defaultdict[tuple[Namespace, Filepath], BinaryMedia]:
        if self.__class__._storage is None:
            raise RuntimeError(
                "Cannot get in-memory storage. InMemoryConnector is not initialized.",
            )
        return self.__class__._storage

    async def put(
        self,
        file: BinaryMedia,
        repo_extra: dict[Any, Any],
        **extra,
    ) -> None:
        namespace = repo_extra["namespace"]
        self.storage[namespace][file.filepath] = file
        logger.info(f"{file=} uploaded to {namespace=}")

    async def get(
        self,
        filepath: Filepath,
        repo_extra: dict[Any, Any],
        **extra: dict[Any, Any],
    ) -> MediaResponse:

        if filepath not in self.storage[repo_extra["namespace"]]:
            return MediaResponse()

        file = self.storage[repo_extra["namespace"]][filepath]

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
        filepath: Filepath,
        repo_extra: dict[Any, Any],
        **extra: dict[Any, Any],
    ):
        self.storage[repo_extra["namespace"]].pop(filepath, None)

    async def copy_object(
        self,
        repo_extra: dict[Any, Any],
        from_filepath: Filepath,
        to_filepath: Filepath,
        to_namespace: Namespace,
        **extra: dict[Any, Any],
    ):
        response = await self.get(
            filepath=from_filepath,
            repo_extra=repo_extra,
        )
        if response:
            self.storage[to_namespace][to_filepath] = response[0]

    @classmethod
    def drop_all(cls) -> None:
        cls.storage = defaultdict(dict)
