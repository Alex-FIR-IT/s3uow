from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from fennflow._operations.context.put import PutContext
from fennflow._operations.dto import OperationRecord
from fennflow._operations.enums import OperationStatusEnum, OperationTypeEnum
from fennflow.backends.enums import OnConflictDoEnum
from fennflow.repositories._validation_mixins.validate_duplicate import (
    ValidateDuplicatesMixin,
)
from fennflow.repositories.at import AtRepository

if TYPE_CHECKING:
    from fennflow.files.types import BinaryMedia


class PutRepository(AtRepository, ValidateDuplicatesMixin):
    """Repository for upserting files in the storage.

    This repository implements the "put" operation, which uploads new files
    to the configured storage (e.g. S3) within the current Unit of Work.

    **Example**::

        file1 = TextContent.from_content("This is the first file.")
        await uow.user_files.at("user1/").put(file1)

    **Behavior**:

    - Each file is registered in the backend as a pending operation
    - Files are uploaded via the connector
    - Backend commit is executed on uow.commit

    **Raises**:
        FilepathsCollisionError:
            If files with the same filepath are passed

    """

    async def put(
        self,
        *files: BinaryMedia,
        **provider_extra,
    ) -> None:
        tasks = []
        self.validate_duplicates_from_files(files)
        for file in files:
            file._storage_prefix = self.cwd

            operation = await self._uow.backend.get_from_current_session(
                file.storage_path
            )

            operation = OperationRecord(
                operation_type=OperationTypeEnum.PUT,
                status=OperationStatusEnum.PENDING,
                storage_path=file.storage_path,
                context=self.__get_context(operation, file),
                session_id=self._uow._session_id,
                repo_extra=self.repo_extra,
            )

            await self._uow.backend.add(
                operation,
                on_conflict=OnConflictDoEnum.REPLACE,
            )
            tasks.append(
                self._uow._operation_executor.execute(
                    operation,
                    **provider_extra,
                ),
            )
        await self._uow.backend.flush()
        await asyncio.gather(*tasks)

    def __get_context(
        self,
        operation: OperationRecord | None,
        file: BinaryMedia,
    ) -> PutContext:
        if (
            operation
            and operation.is_pending
            and operation.session_id == self._uow._session_id
            and operation.is_put_type
        ):
            tmp_path = operation.context.tmp_path
            ctx = PutContext(
                file=file,
                tmp_path=tmp_path,
            )
        else:
            ctx = PutContext(
                file=file,
            )

        return ctx
