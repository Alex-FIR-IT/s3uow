from .abstract import AbstractConnector
from .registry import connector_registry
from .types.config import ConnectorConfig


class ConnectorFactory:
    @staticmethod
    def from_config(config: ConnectorConfig) -> "AbstractConnector":

        connector_cls = connector_registry.get(config.__class__.__name__)
        if not connector_cls:
            raise ValueError(f"Unknown connector for : {type(config)=}")

        return connector_cls(config=config)
