from __future__ import annotations

import datetime
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from uuid import UUID

from fennflow._operations.enums import OperationStatusEnum
from fennflow._sentinel import NOT_GIVEN

if TYPE_CHECKING:
    from fennflow._new_types import Filepath, Namespace
    from fennflow._operations.context.types import Context
    from fennflow._operations.enums import OperationTypeEnum
    from fennflow._sentinel import NotGiven
    from fennflow.repositories.fields.base import RepoExtra


@dataclass(slots=True)
class OperationRecord:
    session_id: uuid.UUID
    filepath: Filepath
    media_type: str
    repo_extra: RepoExtra
    operation_type: OperationTypeEnum
    context: Context
    status: OperationStatusEnum
    operation_id: uuid.UUID = field(default_factory=uuid.uuid4)

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
    error: str | None | NotGiven = NOT_GIVEN

    @property
    def is_pending(self) -> bool:
        return self.status == OperationStatusEnum.PENDING

    @property
    def is_uploaded(self) -> bool:
        return self.status == OperationStatusEnum.UPLOADED

    @property
    def is_failed(self) -> bool:
        return self.status == OperationStatusEnum.FAILED

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
