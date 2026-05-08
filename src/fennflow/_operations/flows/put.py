from __future__ import annotations

from typing import TYPE_CHECKING

from fennflow._operations.enums import OperationStatusEnum
from fennflow._operations.flows.abstract import AbstractFlow

if TYPE_CHECKING:
    from fennflow._operations.context.put import PutContext
    from fennflow._operations.dto import OperationRecord
    from fennflow.connectors.abstract import AbstractConnector


class PutFlow(AbstractFlow):
    @staticmethod
    async def execute(
        *,
        operation: OperationRecord,
        connector: AbstractConnector,
        **provider_extra,
    ):
        ctx: PutContext = operation.context
        return await connector.put(
            file=ctx.file,
            repo_extra=operation.repo_extra,
            **provider_extra,
        )

    @staticmethod
    async def compensate(
        *,
        operation: OperationRecord,
        connector: AbstractConnector,
        **provider_extra,
    ):

        result = await connector.delete(
            filepath=operation.filepath,
            repo_extra=operation.repo_extra,
            **provider_extra,
        )
        operation.status = OperationStatusEnum.FAILED
        return result

    @staticmethod
    async def finalize(
        *,
        operation: OperationRecord,
        connector: AbstractConnector,
        **provider_extra,
    ):
        pass
