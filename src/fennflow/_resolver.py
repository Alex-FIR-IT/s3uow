from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from fennflow.backends.in_memory import InMemoryBackendConfig
from fennflow.connectors import InMemoryConnectorConfig
from fennflow.reconciler import (
    ReconcileConfig,
    ReconcileFrequencyEnum,
    ReconcileStrategyEnum,
)

if TYPE_CHECKING:
    from fennflow import ConfigDict
    from fennflow.backends.types.config import BackendConfig
    from fennflow.connectors.types.config import ConnectorConfig


@dataclass(slots=True)
class ResolvedConfig:
    backend: BackendConfig
    connector: ConnectorConfig
    reconcile: ReconcileConfig


class ConfigResolver:
    @classmethod
    def resolve_config(
        cls,
        config: ConfigDict | None,
    ) -> ResolvedConfig:
        cfg = config or {}
        backend_cfg = cfg.get("backend") or InMemoryBackendConfig()
        reconcile_cfg = cfg.get("reconcile")

        if reconcile_cfg is None:
            reconcile_cfg = cls._get_default_reconcile_config(backend_cfg=backend_cfg)

        return ResolvedConfig(
            backend=backend_cfg,
            connector=cfg.get("connector") or InMemoryConnectorConfig(),
            reconcile=reconcile_cfg,
        )

    @staticmethod
    def _get_default_reconcile_config(backend_cfg: BackendConfig) -> ReconcileConfig:
        # InMemoryBackend loses state on restart —
        # reconcile on every app start by default.

        # Persistent backends (Postgres, Redis, etc.) default to NEVER
        # Since it needs reconciliation on first connection
        default_reconcile = (
            ReconcileConfig(
                frequency=ReconcileFrequencyEnum.ON_START_APP,
                strategy=ReconcileStrategyEnum.FILL_IF_EMPTY,
            )
            if isinstance(backend_cfg, InMemoryBackendConfig)
            else ReconcileConfig()
        )

        return default_reconcile
