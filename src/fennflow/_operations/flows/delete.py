from typing import TYPE_CHECKING

from fennflow._operations.dto import OperationRecord
from fennflow._operations.enums import OperationTypeEnum
from fennflow._operations.flows.abstract import AbstractFlow
from fennflow.connectors.abstract import AbstractConnector

if TYPE_CHECKING:
    from fennflow._operations.context.delete import DeleteContext


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
            from_filepath=operation.filepath,
            from_bucket_name=operation.namespace,
            to_filepath=ctx["to_filepath"],
            to_namespace=ctx["to_namespace"],
            repo_extra=operation.repo_extra,
            **provider_extra,
        )
        return await connector.delete(
            filepath=operation.filepath,
            repo_extra=operation.repo_extra,
            **provider_extra,
        )

    @staticmethod
    async def compensate(
        *,
        operation: "OperationRecord",
        connector: "AbstractConnector",
        **provider_extra,
    ):
        ctx: DeleteContext = operation.context
        await connector.copy_object(
            from_filepath=ctx["to_filepath"],
            from_bucket_name=ctx["to_namespace"],
            to_filepath=operation.filepath,
            to_namespace=operation.namespace,
            repo_extra=operation.repo_extra,
            **provider_extra,
        )
        await connector.delete(
            filepath=ctx["to_filepath"],
            repo_extra=operation.repo_extra,
        )
        operation.status = "uploaded"

    @staticmethod
    async def finalize(
        *,
        operation: "OperationRecord",
        connector: "AbstractConnector",
        **provider_extra,
    ):
        ctx: DeleteContext = operation.context
        await connector.delete(
            filepath=ctx["to_filepath"],
            repo_extra=operation.repo_extra,
            **provider_extra,
        )
