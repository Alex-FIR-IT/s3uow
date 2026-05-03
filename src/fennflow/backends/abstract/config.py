from pydantic import BaseModel, Field


class AbstractBackendConfig(BaseModel):
    namespace: str = Field(
        default="fennflow_backend",
        description="Namespace of backend",
    )
