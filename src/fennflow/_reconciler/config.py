from dataclasses import dataclass

from fennflow._reconciler.enums import ReconcileFrequencyEnum, ReconcileStrategyEnum


@dataclass(slots=True, frozen=True)
class ReconcileConfig:
    frequency: ReconcileFrequencyEnum = ReconcileFrequencyEnum.ON_START_APP
    strategy: ReconcileStrategyEnum = ReconcileStrategyEnum.FILL_IF_EMPTY
    batch_size: int = 1000
