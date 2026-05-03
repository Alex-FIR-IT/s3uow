from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from fennflow import ConfigDict
from fennflow.backends.in_memory import InMemoryBackendConfig
from fennflow.connectors import InMemoryConnectorConfig

if TYPE_CHECKING:
    from fennflow.backends.types.config import BackendConfig
    from fennflow.connectors.types.config import ConnectorConfig


@dataclass(slots=True)
class ResolvedConfig:
    backend: BackendConfig
    connector: ConnectorConfig


def resolve_config(
    config: ConfigDict | None,
) -> ResolvedConfig:
    cfg = config or {}

    return ResolvedConfig(
        backend=cfg.get("backend") or InMemoryBackendConfig(),
        connector=cfg.get("connector") or InMemoryConnectorConfig(),
    )
