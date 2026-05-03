from __future__ import annotations

import asyncio

from fennflow.files.responses.base import MediaResponse
from fennflow.repositories.at import AtRepository


class GetRepository(AtRepository):
    """Repository for retrieving a file from storage within the current scope.

    This method returns a `MediaResponse` object containing the requested file,
    if it exists according to the backend (source of truth).

    **Example**::

        response = await uow.user_files.at("user1/").get("file.txt")
        if response:
            file = response[0]

    **Behavior**:

    - The backend is treated as the source of truth
    - If the file is not present in the backend, the storage is NOT queried
    - If the file exists in the backend,
    it is fetched from the storage via the connector

    **Notes**:

    - This method is read-only and does not participate in transaction flows (no saga)
    - No network request is made if the backend does not contain the file
    - Storage and backend may become inconsistent
      (e.g. after restart with InMemoryBackend);
      in such cases, use a reconcile mechanism to resync state.
      (<add_link_here on wiki>)

    """

    async def get(self, *paths: str, **provider_extra) -> MediaResponse:
        """Retrieve a file from storage within the current scope.

        Args:
            *paths (str):
                Relative file's paths within the scoped repository

            **provider_extra (Any):
                Additional provider-specific parameters passed directly to the connector
                (e.g. S3 `get_object` arguments)

        Returns:
            MediaResponse:
                - `MediaResponse(media=(...))` if the file exists
                - `MediaResponse()` (empty) if the file does not exist
        """
        tasks = []
        for path in paths:
            filepath = self._join_path(path)
            operation = await self._uow.backend.get(
                filepath,
                namespace=self.repo_extra["namespace"],
            )

            if operation:
                tasks.append(
                    self._uow.connector.get(
                        filepath=filepath,
                        repo_extra=self.repo_extra,
                        **provider_extra,
                    )
                )

        if tasks:
            results = await asyncio.gather(*tasks)
            return MediaResponse.join(results)

        return MediaResponse()
