from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from fennflow._operations.context.create import CreateContext
from fennflow._operations.dto import OperationRecord
from fennflow._operations.enums import OperationStatusEnum, OperationTypeEnum
from fennflow.backends.exceptions import RecordAlreadyExistsException
from fennflow.repositories.at import AtRepository

if TYPE_CHECKING:
    from fennflow.files.types import BinaryMedia


class CreateRepository(AtRepository):
    """Repository for uploading (creating) files in the storage.

    This repository implements the "create" operation, which uploads new files
    to the configured storage (e.g. S3) within the current Unit of Work.

    **Example**::

        file1 = TextContent.from_content("This is the first file.")
        await uow.user_files.at("user1/").create(file1)

    **Behavior**:

    - Each file is registered in the backend as a pending operation
    - Files are uploaded via the connector
    - Backend commit is executed on uow.commit

    **Raises**:
        FileAlreadyExistError: If a file with the same path already exists in a backend

    """

    async def create(
        self,
        *files: BinaryMedia,
        **provider_extra,
    ) -> None:
        tasks = []
        for file in files:
            file._storage_prefix = self.cwd

            operation = await self._uow.backend.get(storage_path=file.storage_path)

            if operation:
                raise RecordAlreadyExistsException()

            operation = OperationRecord(
                operation_type=OperationTypeEnum.CREATE,
                status=OperationStatusEnum.PENDING,
                storage_path=file.storage_path,
                context=CreateContext(file=file),
                session_id=self._uow._session_id,
                repo_extra=self.repo_extra,
            )

            await self._uow.backend.add(operation)
            tasks.append(
                self._uow._operation_executor.execute(
                    operation,
                    **provider_extra,
                ),
            )
        await self._uow.backend.flush()
        await asyncio.gather(*tasks)
