from typing import TypeAlias

from fennflow.connectors.in_memory import InMemoryConnectorConfig
from fennflow.connectors.s3 import S3ConnectorConfig

ConnectorConfig: TypeAlias = S3ConnectorConfig | InMemoryConnectorConfig
