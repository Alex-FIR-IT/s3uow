from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import Sequence
from typing import TYPE_CHECKING

from fennflow._operations.executor import OperationExecutor
from fennflow._resolver import resolve_config
from fennflow.backends import BackendFactory
from fennflow.connectors import ConnectorFactory

if TYPE_CHECKING:
    from fennflow import ConfigDict
    from fennflow._operations.dto import OperationRecord
    from fennflow.backends.abstract.base import AbstractBackend
    from fennflow.connectors.abstract import AbstractConnector


logger = logging.getLogger(__name__)


class UnitOfWork:
    """Unit of Work (UOW) — the main entry point of FennFlow.

    It coordinates file operations by managing:
    - backend (operation metadata storage)
    - connector (actual storage, e.g. S3)
    - execution and compensation logic (Saga pattern)

    **Example**::

        async with UOW() as uow:
            await uow.user_files.at("user1/").put(file)

    **Behavior**:
    - By default, `auto_commit=True`:
        commits all operations if the context exits successfully
    - If an exception occurs or `auto_commit=False`:
        triggers rollback with compensation logic

    Example:
        class UOW(UnitOfWork):
            config = ConfigDict(
                backend=PostgresBackendConfig(...),
                connector=S3ConnectorConfig(...),
            )
            user_files = S3RepoField(UserFiles, bucket_name="bucket_name")
            # or
            # user_files = RepoField(UserFiles, namespace="bucket_name")

    Important:
    - Users should NOT interact with backend or connector directly
    - All operations must go through UOW
    - Rollback applies compensation in reverse order (Saga pattern)

    Attributes:
        backend:
            Stores operation metadata (pending, done, failed)

        connector:
            Performs actual storage operations (e.g. S3 API calls)

        operation_executor:
            Executes and compensates operations

    Methods:
        commit():
            Persists operation state via backend

        rollback():
            Runs compensation for all pending operations
            and then rolls back backend state
    """

    config: ConfigDict = None

    def __init__(
        self,
        auto_commit: bool = True,
    ):
        self._auto_commit = auto_commit
        self._session_id = uuid.uuid4()
        resolved = resolve_config(self.config)

        self._backend = BackendFactory.from_config(config=resolved.backend)
        self._connector = ConnectorFactory.from_config(config=resolved.connector)
        self.operation_executor = OperationExecutor(
            connector=self.connector,
        )

    @property
    def backend(self) -> AbstractBackend:
        """Direct access to the backend for read-only inspection.

        Warning: mutating backend state directly bypasses Saga guarantees.
        Use UoW methods for all write operations.
        """
        return self._backend

    @property
    def connector(self) -> AbstractConnector:
        """Direct access to the connector.

        Warning: operations performed directly on the connector
        are not tracked by the backend.
        Therefore, they will not be compensated by uow.
        """
        return self._connector

    async def __aenter__(
        self,
    ):
        await self.connector.open()
        await self.backend.open()
        return self

    async def _finalize_operation(self, operation: OperationRecord) -> None:
        try:
            await self.operation_executor.finalize(operation)
        except Exception:
            logger.warning(
                "Finalization failed.",
                extra={
                    "operation_id": operation.operation_id,
                    "session_id": operation.session_id,
                },
                exc_info=True,
            )

    async def _finalize_operations(self, operations: Sequence[OperationRecord]) -> None:
        await asyncio.gather(
            *(self._finalize_operation(op) for op in operations),
            return_exceptions=True,
        )

    async def commit(
        self,
    ) -> None:
        operations = await self.backend.list_pending()

        for operation in operations:
            await self.backend.mark_done(operation)

        await self.backend.flush()
        await self.backend.clear_session()

        await self._finalize_operations(operations)

    async def rollback(
        self,
    ) -> None:
        operations = await self.backend.list_pending()
        finalize_operations = []
        for operation in reversed(operations):
            try:
                await self.operation_executor.compensate(operation)
            except Exception:
                logger.exception(
                    "Compensation failed.",
                    extra={
                        "operation_id": operation.operation_id,
                        "session_id": operation.session_id,
                    },
                )
                await self.backend.mark_compensation_failed(operation)

            else:
                finalize_operations.append(operation)

        await self.backend.flush()
        await self.backend.clear_session()

        await self._finalize_operations(finalize_operations)

    async def __aexit__(
        self,
        exc_type,
        exc,
        tb,
    ):
        if exc_type is not None or not self._auto_commit:
            await self.rollback()
        elif self._auto_commit:
            await self.commit()

        await self.connector.close()
        await self.backend.close()
