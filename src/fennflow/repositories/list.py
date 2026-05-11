from __future__ import annotations

from fennflow._sentinel import OMIT, Omittable
from fennflow.files.responses.list import ListResponse
from fennflow.repositories.at import AtRepository


class ListRepository(AtRepository):
    """Repository for retrieving a files from storage within the current scope."""

    async def list(
        self,
        prefix: str = "",
        continuation_token: Omittable[str] = OMIT,
        limit: int = 1000,
    ):
        """Uploads files under the current path, optionally filtered by prefix.

        Files are visible if they are uploaded (committed) or pending within the
        current session. Pending files from other sessions are not returned.

        Args:
            prefix: Sub-path to filter results. Appended to the current ``at()``
                path. Defaults to ``""`` (list everything under the current path).
            continuation_token: Opaque token returned by a previous call to
                continue paginating.
            limit: Maximum number of storage_paths to return. Defaults to ``1000``.

        Returns:
            ListResponse: A container of storage_paths matching the query. Includes
                a ``continuation_token`` if more results are available, otherwise
                ``None``.

        Example::

             async with UOW() as uow:
                 await uow.files.at("folder1/").put(file1, file2, file3)
                 page = await uow.files.at("folder1/").list(limit=2)

                 next_page = await uow.files.at("folder1/").list(
                     limit=2,
                     continuation_token=page.continuation_token,
                 )
        """
        storage_prefix = self._join_path(prefix)

        operation_page = await self._uow.backend.get_visible(
            prefix=storage_prefix,
            continuation_token=continuation_token,
            limit=limit,
            session_id=self._uow._session_id,
        )

        return ListResponse(
            storage_paths=tuple(op.storage_path for op in operation_page),
            continuation_token=operation_page.continuation_token,
        )
