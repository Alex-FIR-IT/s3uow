from __future__ import annotations

from typing import TYPE_CHECKING

from .._operations.dto import OperationRecord
from .._operations.enums import OperationTypeEnum
from .at import AtRepository

if TYPE_CHECKING:
    from .._operations.context.delete import DeleteContext


class DeleteRepository(AtRepository):
    async def delete(self, path: str, **provider_extra) -> bool:
        filepath = self._join_path(path)
        operation = await self._uow.backend.get(
            filepath,
            namespace=self.repo_extra["namespace"],
        )

        if operation is None:
            return False

        context: DeleteContext = {
            "to_filepath": self._join_path(
                "tmp",
                f"session_id_{operation.session_id}",
                f"operation_id_{operation.session_id}",
                self._path,
                path,
            ),
            "to_namespace": self.repo_extra["namespace"],
        }

        operation = OperationRecord(
            operation_type=OperationTypeEnum.DELETE,
            media_type=operation.media_type,
            status="pending",
            filepath=operation.filepath,
            context=context,
            session_id=self._uow._session_id,
            repo_extra=self.repo_extra,
        )
        await self._uow.backend.add(operation)

        await self._uow.operation_executor.execute(operation)
        await self._uow.backend.flush()
        return True
