from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from fennflow._decorators import reraise_with
from fennflow._operations.dto import OperationRecord
from fennflow._operations.enums import OperationStatusEnum, OperationTypeEnum
from fennflow._reconciler.enums import ReconcileStrategyEnum
from fennflow._reconciler.exceptions import ReconcileFailedException
from fennflow.backends.enums import OnConflictDoEnum
from fennflow.repositories import RepoField

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Generator, Iterable
    from uuid import UUID

    from fennflow import UnitOfWork
    from fennflow.backends.abstract.base import AbstractBackend
    from fennflow.connectors.abstract import AbstractConnector
    from fennflow.files.responses.list import ListResponse
    from fennflow.repositories.fields.base import RepoExtra

logger = logging.getLogger(__name__)


reconcile_to_on_conflict_strategy = {
    ReconcileStrategyEnum.REPLACE: OnConflictDoEnum.REPLACE,
    ReconcileStrategyEnum.INSERT_MISSING: OnConflictDoEnum.DO_NOTHING,
    ReconcileStrategyEnum.FILL_IF_EMPTY: OnConflictDoEnum.RAISE,
}


class Reconciler:
    def __init__(
        self,
        uow_fields: Iterable[RepoField],
        backend: AbstractBackend,
        connector: AbstractConnector,
    ) -> None:
        self.uow_fields = uow_fields
        self.backend = backend
        self.connector = connector

    @reraise_with(ReconcileFailedException())
    async def reconcile(
        self,
        session_id: UUID,
        strategy: ReconcileStrategyEnum,
        batch_size: int,
    ) -> None:
        for repo in self.uow_fields:
            if not await self._should_reconcile(strategy=strategy):
                continue

            on_conflict = reconcile_to_on_conflict_strategy[strategy]

            async for page in self._iter_pages(repo, batch_size=batch_size):
                await self.backend.insert(
                    operations=self._records_from_page(
                        session_id=session_id,
                        page=page,
                        repo_extra=repo.repo_extra,
                    ),
                    on_conflict=on_conflict,
                )

    async def _should_reconcile(self, strategy: ReconcileStrategyEnum) -> bool:
        if strategy == ReconcileStrategyEnum.FILL_IF_EMPTY:
            return await self.backend.is_empty()
        return True

    async def _iter_pages(
        self,
        repo: RepoField,
        batch_size: int,
    ) -> AsyncGenerator[ListResponse, None]:
        continuation_token = None

        while True:
            page = await self.connector.list_objects(
                prefix="",
                limit=batch_size,
                repo_extra=repo.repo_extra,
                continuation_token=continuation_token,
            )
            yield page

            if page.continuation_token is None:
                break
            continuation_token = page.continuation_token

    @staticmethod
    def _records_from_page(
        session_id: UUID,
        page: ListResponse,
        repo_extra: RepoExtra,
    ) -> Generator[OperationRecord, None, None]:
        for storage_path in page:
            yield OperationRecord(
                session_id=session_id,
                storage_path=storage_path,
                operation_type=OperationTypeEnum.PUT,
                status=OperationStatusEnum.UPLOADED,
                repo_extra=repo_extra,
            )

    @staticmethod
    def _get_repo_fields(uow: UnitOfWork) -> Generator[RepoField, None, None]:
        for field in vars(type(uow)).values():
            if isinstance(field, RepoField):
                yield field
