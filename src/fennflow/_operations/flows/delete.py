from __future__ import annotations

from typing import TYPE_CHECKING

from fennflow._operations.enums import OperationStatusEnum
from fennflow._operations.flows.abstract import AbstractFlow

if TYPE_CHECKING:
    from fennflow._operations.context.delete import DeleteContext
    from fennflow._operations.dto import OperationRecord
    from fennflow.connectors.abstract import AbstractConnector


class DeleteFlow(AbstractFlow):
    @staticmethod
    async def execute(
        *,
        operation: OperationRecord,
        connector: AbstractConnector,
        **provider_extra,
    ):
        ctx: DeleteContext = operation.context
        await connector.copy_object(
            from_storage_path=operation.storage_path,
            from_bucket_name=operation.namespace,
            to_storage_path=ctx.to_storage_path,
            to_namespace=ctx.to_namespace,
            repo_extra=operation.repo_extra,
            **provider_extra,
        )
        return await connector.delete(
            storage_path=operation.storage_path,
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
        ctx: DeleteContext = operation.context
        await connector.copy_object(
            from_storage_path=ctx.to_storage_path,
            from_bucket_name=ctx.to_namespace,
            to_storage_path=operation.storage_path,
            to_namespace=operation.namespace,
            repo_extra=operation.repo_extra,
            **provider_extra,
        )
        await connector.delete(
            storage_path=ctx.to_storage_path,
            repo_extra=operation.repo_extra,
        )
        operation.status = OperationStatusEnum.UPLOADED

    @staticmethod
    async def finalize(
        *,
        operation: OperationRecord,
        connector: AbstractConnector,
        **provider_extra,
    ):
        ctx: DeleteContext = operation.context
        await connector.delete(
            storage_path=ctx.to_storage_path,
            repo_extra=operation.repo_extra,
            **provider_extra,
        )
