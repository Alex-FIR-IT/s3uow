from __future__ import annotations

from typing import TYPE_CHECKING

from .registry import flow_registry

if TYPE_CHECKING:
    from fennflow.connectors.abstract import AbstractConnector

    from .dto import OperationRecord


class OperationExecutor:
    def __init__(self, connector: AbstractConnector) -> None:
        self.connector = connector

    async def execute(
        self,
        operation: OperationRecord,
        **provider_extra,
    ):
        operation_flow = flow_registry[operation.operation_type]
        return await operation_flow().execute(
            operation=operation,
            connector=self.connector,
            **provider_extra,
        )

    async def compensate(
        self,
        operation: OperationRecord,
    ):
        operation_flow = flow_registry[operation.operation_type]
        return await operation_flow().compensate(
            operation=operation,
            connector=self.connector,
        )

    async def finalize(
        self,
        operation: OperationRecord,
    ):
        operation_flow = flow_registry[operation.operation_type]
        return await operation_flow().finalize(
            operation=operation,
            connector=self.connector,
        )
