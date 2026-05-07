from __future__ import annotations

from typing import TYPE_CHECKING, NotRequired, TypedDict

if TYPE_CHECKING:
    from uuid import UUID

    from fennflow._new_types import Filepath
    from fennflow._operations.enums import OperationStatusEnum


class SelectParams(TypedDict):
    path: NotRequired[Filepath]
    prefix: NotRequired[str]
    status: NotRequired[OperationStatusEnum]
    media_type: NotRequired[str]
    session_id: NotRequired[UUID]
    operation_id: NotRequired[UUID]
    is_expired: NotRequired[bool]
    limit: NotRequired[int]
    continuation_token: NotRequired[str]
    visible_for_session_id: NotRequired[UUID]
