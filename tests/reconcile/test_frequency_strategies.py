from contextlib import nullcontext
from uuid import uuid4

import pytest

from fennflow import ConfigDict, UnitOfWork
from fennflow._operations.dto import OperationRecord
from fennflow._operations.enums import OperationStatusEnum, OperationTypeEnum
from fennflow._reconciler import (
    ReconcileConfig,
    ReconcileFrequencyEnum,
    ReconcileStrategyEnum,
)
from fennflow.backends import InMemoryBackend, InMemoryBackendConfig
from fennflow.connectors import InMemoryConnector
from fennflow.repositories import RepoField
from tests.conftest import UserFiles


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "frequency, strategy, prefill_backend, response_len, files_assertion, expected_exception",
    [
        # ON_START_APP combinations
        (
            ReconcileFrequencyEnum.ON_START_APP,
            ReconcileStrategyEnum.FILL_IF_EMPTY,
            False,
            2,
            True,
            nullcontext(),
        ),
        (
            ReconcileFrequencyEnum.ON_START_APP,
            ReconcileStrategyEnum.FILL_IF_EMPTY,
            True,
            1,
            False,
            nullcontext(),
        ),
        (
            ReconcileFrequencyEnum.ON_START_APP,
            ReconcileStrategyEnum.REPLACE,
            False,
            2,
            True,
            nullcontext(),
        ),
        (
            ReconcileFrequencyEnum.ON_START_APP,
            ReconcileStrategyEnum.REPLACE,
            True,
            2,
            True,
            nullcontext(),
        ),
        (
            ReconcileFrequencyEnum.ON_START_APP,
            ReconcileStrategyEnum.INSERT_MISSING,
            False,
            2,
            True,
            nullcontext(),
        ),
        (
            ReconcileFrequencyEnum.ON_START_APP,
            ReconcileStrategyEnum.INSERT_MISSING,
            True,
            2,
            True,
            nullcontext(),
        ),
        # ON_SESSION_START combinations
        (
            ReconcileFrequencyEnum.ON_SESSION_START,
            ReconcileStrategyEnum.FILL_IF_EMPTY,
            False,
            2,
            True,
            nullcontext(),
        ),
        (
            ReconcileFrequencyEnum.ON_SESSION_START,
            ReconcileStrategyEnum.FILL_IF_EMPTY,
            True,
            1,
            False,
            nullcontext(),
        ),
        (
            ReconcileFrequencyEnum.ON_SESSION_START,
            ReconcileStrategyEnum.REPLACE,
            False,
            2,
            True,
            nullcontext(),
        ),
        (
            ReconcileFrequencyEnum.ON_SESSION_START,
            ReconcileStrategyEnum.REPLACE,
            True,
            2,
            True,
            nullcontext(),
        ),
        (
            ReconcileFrequencyEnum.ON_SESSION_START,
            ReconcileStrategyEnum.INSERT_MISSING,
            False,
            2,
            True,
            nullcontext(),
        ),
        (
            ReconcileFrequencyEnum.ON_SESSION_START,
            ReconcileStrategyEnum.INSERT_MISSING,
            True,
            2,
            True,
            nullcontext(),
        ),
        # NEVER combinations
        (
            ReconcileFrequencyEnum.NEVER,
            ReconcileStrategyEnum.FILL_IF_EMPTY,
            False,
            0,
            False,
            nullcontext(),
        ),
        (
            ReconcileFrequencyEnum.NEVER,
            ReconcileStrategyEnum.FILL_IF_EMPTY,
            True,
            1,
            False,
            nullcontext(),
        ),
        (
            ReconcileFrequencyEnum.NEVER,
            ReconcileStrategyEnum.REPLACE,
            False,
            0,
            False,
            nullcontext(),
        ),
        (
            ReconcileFrequencyEnum.NEVER,
            ReconcileStrategyEnum.REPLACE,
            True,
            1,
            False,
            nullcontext(),
        ),
        (
            ReconcileFrequencyEnum.NEVER,
            ReconcileStrategyEnum.INSERT_MISSING,
            False,
            0,
            False,
            nullcontext(),
        ),
        (
            ReconcileFrequencyEnum.NEVER,
            ReconcileStrategyEnum.INSERT_MISSING,
            True,
            1,
            False,
            nullcontext(),
        ),
    ],
)
async def test_reconcile_on_non_empty_connector(
    frequency,
    strategy,
    prefill_backend,
    response_len,
    files_assertion,
    expected_exception,
    text_files,
):
    backend_namespace = "fennflow_backend"

    class TestUOW(UnitOfWork):
        user_files = RepoField(UserFiles, namespace="user_files")
        config = ConfigDict(
            reconcile=ReconcileConfig(frequency=frequency, strategy=strategy),
            backend=InMemoryBackendConfig(namespace=backend_namespace),
        )

    if prefill_backend:
        InMemoryBackend._storage[backend_namespace][text_files[0].filename] = (
            OperationRecord(
                session_id=uuid4(),
                filepath=text_files[0].filename,
                status=OperationStatusEnum.UPLOADED,
                operation_type=OperationTypeEnum.PUT,
                repo_extra=TestUOW.user_files.repo_extra,
            )
        )

    for text_file in text_files:
        InMemoryConnector._storage[TestUOW.user_files.repo_extra["namespace"]][
            text_file.filename
        ] = text_file

    with expected_exception:
        async with TestUOW() as uow:
            response = await uow.user_files.list()

            assert len(response) == response_len

            files = []
            for filepath in response:
                response = await uow.user_files.get(filepath)
                files.extend(response)

            files_equal = sorted(files) == sorted(text_files)
            assert files_equal == files_assertion
