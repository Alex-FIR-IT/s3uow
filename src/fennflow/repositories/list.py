from __future__ import annotations

from fennflow._operations.enums import OperationStatusEnum
from fennflow._sentinel import OMIT, Omittable
from fennflow.files.responses.list import ListResponse
from fennflow.repositories.at import AtRepository


class ListRepository(AtRepository):
    async def list(
        self,
        prefix: str = "",
        continuation_token: Omittable[str] = OMIT,
        limit: int = 1000,
    ):
        folder_path = self._join_path(prefix)

        operation_page = await self._uow.backend.get_visible(
            prefix=folder_path,
            continuation_token=continuation_token,
            limit=limit,
            session_id=self._uow._session_id,
        )

        return ListResponse(
            filepaths=tuple(op.filepath for op in operation_page),
            continuation_token=operation_page.continuation_token,
        )
