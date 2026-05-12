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
