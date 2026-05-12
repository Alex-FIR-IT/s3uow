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
