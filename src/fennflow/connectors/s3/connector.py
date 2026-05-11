from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Self

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

    from fennflow._new_types import Filepath, Namespace
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
            Key=file.filepath,
            Body=file.data,
            ContentType=file.media_type,
            Metadata=file.get_metadata(),
            **sdk_extra,
        )
        logger.info(f"{file=} uploaded to {bucket_name=}")

    async def get(
        self,
        filepath: Filepath,
        repo_extra: S3Extra,
        **sdk_extra: Any,
    ) -> MediaResponse:
        response = await self.s3client.client.get_object(
            Bucket=repo_extra["namespace"],
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
        filepath: Filepath,
        repo_extra: S3Extra,
        **sdk_extra: Any,
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
        from_filepath: Filepath,
        to_filepath: Filepath,
        to_namespace: Namespace,
        **sdk_extra: Any,
    ):
        bucket_name = repo_extra["namespace"]

        await self.s3client.client.copy_object(
            CopySource={"Bucket": bucket_name, "Key": from_filepath},
            Bucket=to_namespace,
            Key=to_filepath,
            **sdk_extra,
        )
        logger.info(
            f"file from {bucket_name=} with {from_filepath=} copied to {to_namespace=}"
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
            filepaths=tuple(obj["Key"] for obj in response.get("Contents", [])),
            continuation_token=response.get("NextContinuationToken"),
        )
