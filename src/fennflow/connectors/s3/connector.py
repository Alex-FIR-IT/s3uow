from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Self

from aiobotocore.session import get_session

from fennflow.connectors.abstract import AbstractConnector
from fennflow.connectors.s3.client import S3Client
from fennflow.files import ContentFactory
from fennflow.files.responses.base import MediaResponse
from fennflow.files.types import BinaryMedia

if TYPE_CHECKING:
    from aiobotocore.session import AioSession

    from ...repositories.fields.s3 import S3Extra
    from . import S3ConnectorConfig

logger = logging.getLogger(__name__)


class S3Connector(AbstractConnector):
    aio_session: AioSession = None

    async def open(
        self,
    ) -> Self:
        if self.__class__.aio_session is None:
            self.__class__.aio_session = get_session()

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

    def __init__(
        self,
        config: S3ConnectorConfig,
    ):
        self._config = config
        self._client: S3Client | None = None

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
        **sdk_extra: dict[Any, Any],
    ) -> None:
        bucket_name = repo_extra["namespace"]
        await self.s3client.client.put_object(
            Bucket=bucket_name,
            Key=file.filepath,
            Body=file.data,
            ContentType=file.media_type,
            Metadata=file.get_metadata(),
            **sdk_extra,
        )
        logger.info(f"{file=} uploaded to {bucket_name=}")

    async def get(
        self,
        filepath: str,
        repo_extra: S3Extra,
        **sdk_extra: dict[Any, Any],
    ) -> MediaResponse:
        response = await self.s3client.client.get_object(
            Bucket=repo_extra["bucket_name"],
            Key=filepath,
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
        filepath: str,
        repo_extra: S3Extra,
        **sdk_extra: dict[Any, Any],
    ):
        bucket_name = repo_extra["namespace"]
        await self.s3client.client.delete_object(
            Bucket=bucket_name,
            Key=filepath,
            **sdk_extra,
        )
        logger.info(f"file with {filepath=} deleted from {bucket_name=}")

    async def copy_object(
        self,
        repo_extra: S3Extra,
        from_filepath: str,
        to_filepath: str,
        to_namespace: str,
        **sdk_extra: dict[Any, Any],
    ):
        bucker_name = repo_extra["bucket_name"]

        await self.s3client.client.copy_object(
            CopySource={"Bucket": bucker_name, "Key": from_filepath},
            Bucket=to_namespace,
            Key=to_filepath,
            **sdk_extra,
        )
        logger.info(
            f"file from {bucker_name=} with {from_filepath=} copied to {to_namespace=}"
        )
