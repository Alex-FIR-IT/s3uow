from unittest.mock import AsyncMock, MagicMock

import pytest

from fennflow._reconciler import Reconciler, ReconcileStrategyEnum


@pytest.mark.parametrize(
    "strategy, is_empty_val, expected",
    [
        (
            ReconcileStrategyEnum.FILL_IF_EMPTY,
            True,
            True,
        ),
        (
            ReconcileStrategyEnum.FILL_IF_EMPTY,
            False,
            False,
        ),
        (
            ReconcileStrategyEnum.REPLACE,
            False,
            True,
        ),
        (
            ReconcileStrategyEnum.REPLACE,
            True,
            True,
        ),
        (
            ReconcileStrategyEnum.INSERT_MISSING,
            False,
            True,
        ),
        (
            ReconcileStrategyEnum.INSERT_MISSING,
            True,
            True,
        ),
    ],
)
@pytest.mark.asyncio
async def test_should_reconcile(strategy, is_empty_val, expected):
    mock_self = MagicMock()
    mock_self.backend.is_empty = AsyncMock(return_value=is_empty_val)

    result = await Reconciler._should_reconcile(mock_self, strategy)

    assert result is expected
