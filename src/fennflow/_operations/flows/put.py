from fennflow._operations.context.put import PutContext
from fennflow._operations.dto import OperationRecord
from fennflow._operations.enums import OperationTypeEnum
from fennflow._operations.flows.abstract import AbstractFlow
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
            file=ctx["file"],
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

        result = await connector.delete(
            filepath=operation.filepath,
            repo_extra=operation.repo_extra,
            **provider_extra,
        )
        operation.status = "failed"
        return result

    @staticmethod
    async def finalize(
        *,
        operation: "OperationRecord",
        connector: "AbstractConnector",
        **provider_extra,
    ):
        pass
