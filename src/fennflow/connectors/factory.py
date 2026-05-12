from __future__ import annotations

from typing import TYPE_CHECKING

from .registry import connector_registry

if TYPE_CHECKING:
    from .abstract import AbstractConnector
    from .types.config import ConnectorConfig


class ConnectorFactory:
    """Factory for creating connector instances from config objects.

    Resolves the appropriate connector class from ``connector_registry``
    based on the config class name.

    Example::

        connector = ConnectorFactory.from_config(S3ConnectorConfig(...))
    """

    @staticmethod
    def from_config(config: ConnectorConfig) -> AbstractConnector:
        """Create a connector instance from a config object.

        Args:
            config: The connector configuration instance.

        Returns:
            An initialized connector instance.

        Raises:
            ValueError: If no connector is registered for the config type.
        """
        connector_cls = connector_registry.get(config.__class__.__name__)
        if not connector_cls:
            raise ValueError(f"Unknown connector for : {type(config)=}")

        return connector_cls(config=config)
