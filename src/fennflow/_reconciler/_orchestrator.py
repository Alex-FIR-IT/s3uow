from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, ClassVar

from fennflow._reconciler.core import Reconciler
from fennflow._reconciler.enums import ReconcileFrequencyEnum
from fennflow.uow.inspector import UowInspector

if TYPE_CHECKING:
    from fennflow import UnitOfWork
    from fennflow._new_types import UowQualName

logger = logging.getLogger(__name__)


class ReconcileOrchestrator:
    _reconciled_on_startup: ClassVar[set[UowQualName]] = set()
    _lock: asyncio.Lock = asyncio.Lock()

    async def reconcile_if_needed(self, uow: UnitOfWork) -> None:
        frequency = uow._resolved_config.reconcile.frequency

        async with self._lock:
            match frequency:
                case ReconcileFrequencyEnum.NEVER:
                    await self._handle_never(uow=uow)
                case ReconcileFrequencyEnum.ON_START_APP:
                    await self._handle_on_start_app(uow=uow)
                case ReconcileFrequencyEnum.ON_SESSION_START:
                    await self._handle_on_session_start(uow=uow)
                case _:
                    raise AssertionError("Unhandled frequency")

    async def _handle_never(self, uow: UnitOfWork) -> None:
        logger.debug(
            "Skipping reconciliation.",
            extra=self._log_extra(uow),
        )

    async def _handle_on_start_app(self, uow: UnitOfWork) -> None:
        if uow.__class__.__qualname__ in self._reconciled_on_startup:
            logger.debug(
                "Skipping reconciliation.",
                extra=self._log_extra(uow=uow),
            )
            return

        logger.debug(
            "Starting reconciliation...",
            extra=self._log_extra(uow=uow),
        )
        await self._reconcile(uow=uow)
        self._reconciled_on_startup.add(uow.__class__.__qualname__)

    async def _handle_on_session_start(self, uow: UnitOfWork) -> None:
        logger.debug("Starting reconciliation...", extra=self._log_extra(uow=uow))
        await self._reconcile(uow=uow)

    async def _reconcile(self, uow: UnitOfWork) -> None:
        extractor = UowInspector(uow=uow)
        reconcile = Reconciler(
            uow_fields=extractor.get_repo_fields(),
            connector=uow.connector,
            backend=uow.backend,
        )

        await reconcile.reconcile(
            session_id=uow._session_id,
            batch_size=uow._resolved_config.reconcile.batch_size,
            strategy=uow._resolved_config.reconcile.strategy,
        )

        logger.debug(
            "Finished reconciliation.",
            extra=self._log_extra(uow=uow),
        )

    @staticmethod
    def _log_extra(uow: UnitOfWork) -> dict[str, Any]:
        return {
            "session_id": uow._session_id,
            "uow_class_name": uow.__class__.__qualname__,
            "frequency": uow._resolved_config.reconcile.frequency,
        }
