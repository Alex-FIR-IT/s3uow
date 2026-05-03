from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from aiobotocore.session import AioSession, ClientCreatorContext
    from types_aiobotocore_s3 import S3Client as S3ClientAiobotocore

    from fennflow.connectors.s3 import S3ConnectorConfig


logger = logging.getLogger(__name__)


class S3Client:
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
