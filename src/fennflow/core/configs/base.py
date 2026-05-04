from typing_extensions import TypedDict

from fennflow.backends.types.config import BackendConfig
from fennflow.connectors.types.config import ConnectorConfig


class ConfigDict(TypedDict, total=False):
    """Configuration for a UnitOfWork instance.

    All fields are optional — if not provided, defaults are used.

    Attributes:
        backend: Configuration for the metadata backend
            (e.g. ``InMemoryBackendConfig``).
        connector: Configuration for the storage connector (e.g. ``S3ConnectorConfig``).

    Example:
        class UOW(UnitOfWork):
            config = ConfigDict(
                backend=InMemoryBackendConfig(),
                connector=S3ConnectorConfig(...),
            )
    """

    backend: BackendConfig
    connector: ConnectorConfig
