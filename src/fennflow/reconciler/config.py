from dataclasses import dataclass

from fennflow.reconciler.enums import ReconcileFrequencyEnum, ReconcileStrategyEnum


@dataclass(slots=True, frozen=True)
class ReconcileConfig:
    """Configuration for the reconciler."""

    frequency: ReconcileFrequencyEnum = ReconcileFrequencyEnum.ON_START_APP
    strategy: ReconcileStrategyEnum = ReconcileStrategyEnum.FILL_IF_EMPTY
    batch_size: int = 1000
