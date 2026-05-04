from pydantic import BaseModel


class InMemoryConnectorConfig(BaseModel):
    """Configuration for the in-memory connector.

    No configuration is required — the in-memory connector
    is zero-dependency and is intended for testing and development only.
    """
