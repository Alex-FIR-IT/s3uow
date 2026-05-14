# Reconciler

The reconciler re-syncs the backend with what the file storage actually contains.
Without reconciliation, the backend would report no files exist even though the storage is full — making everything
invisible to `GetRepository`,  `ListRepository`, etc.

## When it runs

Reconciliation is configured via `ReconcileConfig` inside `ConfigDict`. These are default settings:

```python
from fennflow.reconciler import ReconcileConfig, ReconcileFrequencyEnum, ReconcileStrategyEnum


class UOW(UnitOfWork):
    config = ConfigDict(
        reconcile=ReconcileConfig(
            frequency=ReconcileFrequencyEnum.ON_START_APP,
            strategy=ReconcileStrategyEnum.FILL_IF_EMPTY,
            batch_size=1000,
            ),
        )
```

**Frequency options:**

| Value              | Behavior                                     |
|--------------------|----------------------------------------------|
| `ON_START_APP`     | Runs once per process lifetime per UoW class |
| `ON_SESSION_START` | Runs on every `async with UOW()` entry       |
| `NEVER`            | Disabled                                     |

**Strategy options:**

| Value            | Behavior                                                                                                           |
|------------------|--------------------------------------------------------------------------------------------------------------------|
| `FILL_IF_EMPTY`  | Only reconciles if the backend has no records at all                                                               |
| `INSERT_MISSING` | Inserts records for files found in storage that the backend doesn't know about, leaving existing records untouched |
| `REPLACE`        | Replaces all backend state with what storage contains                                                              |

## What the reconciler does

On trigger, the reconciler iterates all `RepoField` instances declared on the UoW class. For each one, it paginates
through the file storage (via the connector's `list_objects`) and inserts the found paths into the backend as `UPLOADED`
records, according to the chosen conflict strategy.

> More info here - [Core Concepts — Reconciler](../advanced_features/reconciler.md).
