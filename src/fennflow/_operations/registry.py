from __future__ import annotations

from typing import TYPE_CHECKING

from .enums import OperationTypeEnum
from .flows.delete import DeleteFlow
from .flows.put import PutFlow

if TYPE_CHECKING:
    from .flows.abstract import AbstractFlow

flow_registry: dict[OperationTypeEnum | str, type[AbstractFlow]] = {
    OperationTypeEnum.PUT: PutFlow,
    OperationTypeEnum.DELETE: DeleteFlow,
}
