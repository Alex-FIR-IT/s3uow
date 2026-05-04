from pydantic import BaseModel, Field


class AbstractBackendConfig(BaseModel):
    """Base configuration for all FennFlow backends."""

    namespace: str = Field(
        default="fennflow_backend",
        description="Namespace of backend. "
        "Useful to distinguish between backends for different file storages.",
    )
