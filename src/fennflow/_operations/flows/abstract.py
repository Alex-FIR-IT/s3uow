from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fennflow._operations.dto import OperationRecord
    from fennflow.connectors.abstract import AbstractConnector


class AbstractFlow(ABC):
    @staticmethod
    @abstractmethod
    async def execute(
        *,
        operation: "OperationRecord",
        connector: "AbstractConnector",
        **provider_extra,
    ): ...

    @staticmethod
    @abstractmethod
    async def compensate(
        *,
        operation: "OperationRecord",
        connector: "AbstractConnector",
    ): ...

    @staticmethod
    @abstractmethod
    async def finalize(
        *,
        operation: "OperationRecord",
        connector: "AbstractConnector",
    ): ...
