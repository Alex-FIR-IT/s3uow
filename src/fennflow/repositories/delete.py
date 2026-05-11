from __future__ import annotations

from fennflow._operations.context.delete import DeleteContext
from fennflow._operations.dto import OperationRecord
from fennflow._operations.enums import OperationStatusEnum, OperationTypeEnum

from .at import AtRepository


class DeleteRepository(AtRepository):
    """Repository mixin for deleting files from storage.

    Implements Saga-based deletion with automatic compensation on failure.
    """

    async def delete(self, path: str, **provider_extra) -> bool:
        """Delete a file from storage.

        Args:
            path: Path to the file relative to the current directory.
            **provider_extra: Additional kwargs forwarded to the connector.

        Returns:
            True if the file was deleted, False if it did not exist.

        """
        storage_path = self._join_path(path)
        operation = await self._uow.backend.get(storage_path)

        if operation is None or not operation.is_visible(self._uow._session_id):
            return False

        context = DeleteContext(
            to_storage_path=self._join_path(
                "tmp",
                f"session_id_{operation.session_id}",
                f"operation_id_{operation.session_id}",
                self._path,
                path,
            ),
            to_namespace=self.repo_extra["namespace"],
        )

        operation = OperationRecord(
            operation_type=OperationTypeEnum.DELETE,
            status=OperationStatusEnum.PENDING,
            storage_path=operation.storage_path,
            context=context,
            session_id=self._uow._session_id,
            repo_extra=self.repo_extra,
        )
        await self._uow.backend.add(operation)

        await self._uow.operation_executor.execute(
            operation,
            **provider_extra,
        )
        await self._uow.backend.flush()
        return True
