from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING

from fennflow._operations.enums import OperationStatusEnum
from fennflow._operations.flows.abstract import AbstractFlow
from fennflow._sentinel import is_given
from fennflow.connectors.exceptions import NoSuchKeyException

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

        if not is_given(ctx.tmp_path):
            tmp_path = operation.generate_tmp_path()

            with suppress(NoSuchKeyException):
                await connector.copy_object(
                    from_storage_path=operation.storage_path,
                    to_storage_path=tmp_path,
                    to_namespace=operation.repo_extra["namespace"],
                    repo_extra=operation.repo_extra,
                    **provider_extra,
                )
                ctx.tmp_path = tmp_path

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

        ctx: PutContext = operation.context

        if is_given(ctx.tmp_path):
            await connector.copy_object(
                from_storage_path=ctx.tmp_path,
                to_storage_path=operation.storage_path,
                to_namespace=operation.namespace,
                repo_extra=operation.repo_extra,
                **provider_extra,
            )
            operation.status = OperationStatusEnum.UPLOADED
        else:
            await connector.delete(
                storage_path=operation.storage_path,
                repo_extra=operation.repo_extra,
                **provider_extra,
            )
            operation.status = OperationStatusEnum.FAILED

    @staticmethod
    async def finalize(
        *,
        operation: OperationRecord,
        connector: AbstractConnector,
        **provider_extra,
    ):

        ctx: PutContext = operation.context

        if is_given(ctx.tmp_path):
            await connector.delete(
                storage_path=ctx.tmp_path,
                repo_extra=operation.repo_extra,
                **provider_extra,
            )
