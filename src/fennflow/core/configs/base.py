from typing_extensions import TypedDict

from fennflow.backends.types.config import BackendConfig
from fennflow.connectors.types.config import ConnectorConfig


class ConfigDict(TypedDict, total=False):
    backend: BackendConfig
    connector: ConnectorConfig
