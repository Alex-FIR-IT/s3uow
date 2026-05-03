from __future__ import annotations

import datetime
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal
from uuid import UUID

from fennflow._new_types import Namespace
from fennflow._sentinel import NOT_GIVEN

if TYPE_CHECKING:
    from fennflow._operations.context.types import Context
    from fennflow._operations.enums import OperationTypeEnum


@dataclass(slots=True)
class OperationRecord:
    operation_id: uuid.UUID = field(default_factory=uuid.uuid4)
    session_id: uuid.UUID = NOT_GIVEN
    filepath: str = NOT_GIVEN
    media_type: str = NOT_GIVEN
    repo_extra: dict = NOT_GIVEN
    operation_type: OperationTypeEnum = NOT_GIVEN
    status: Literal[
        "pending", "uploaded", "failed", "compensation_failed", "deleted"
    ] = NOT_GIVEN
    created_at: datetime.datetime = field(
        default_factory=lambda: datetime.datetime.now(tz=datetime.UTC)
    )
    updated_at: datetime.datetime = field(
        default_factory=lambda: datetime.datetime.now(tz=datetime.UTC)
    )
    expired_at: datetime.datetime = field(
        default_factory=lambda: (
            datetime.datetime.now(tz=datetime.UTC) + datetime.timedelta(seconds=30)
        )
    )
    error: str | None = None
    context: Context = NOT_GIVEN

    @property
    def is_pending(self) -> bool:
        return self.status == "pending"

    @property
    def is_uploaded(self) -> bool:
        return self.status == "uploaded"

    @property
    def is_failed(self) -> bool:
        return self.status == "failed"

    @property
    def namespace(self) -> Namespace:
        return self.repo_extra["namespace"]

    @property
    def is_expired(self):
        return self.expired_at < datetime.datetime.now(tz=datetime.UTC)

    @property
    def is_dangling(self) -> bool:
        return self.is_expired and not self.is_uploaded

    def is_locked(self, current_session_id: UUID) -> bool:
        return (
            self.session_id != current_session_id
            and self.is_pending
            and not self.is_expired
        )
