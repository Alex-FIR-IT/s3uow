from aiobotocore.config import AioConfig
from pydantic import BaseModel, ConfigDict


class S3ConnectorConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    endpoint_url: str | None = None
    aiobotocore_config: AioConfig | None = None
