from pydantic import BaseModel, Field

from fennflow._new_types import Namespace


class AbstractBackendConfig(BaseModel):
    """Base configuration for all FennFlow backends."""

    namespace: Namespace = Field(
        default="fennflow_backend",
        description="Namespace of backend. "
        "Useful to distinguish between backends for different file storages.",
    )
