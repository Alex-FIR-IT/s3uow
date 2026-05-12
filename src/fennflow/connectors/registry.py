from fennflow.connectors.in_memory.config import InMemoryConnectorConfig
from fennflow.connectors.in_memory.connector import InMemoryConnector
from fennflow.connectors.s3.config import S3ConnectorConfig
from fennflow.connectors.s3.connector import S3Connector

connector_registry = {
    S3ConnectorConfig.__name__: S3Connector,
    InMemoryConnectorConfig.__name__: InMemoryConnector,
}
