# Reconciler — Manual Usage

> New to the reconciler? Start with [Core Concepts — Reconciler](../core_concepts/reconciler.md) first.

By default, reconciliation is triggered automatically on UoW entry according to `ReconcileConfig`. In some cases you may
want to trigger it manually — for example, to force a `REPLACE` sync mid-session after an external process has modified
the storage directly, or to reconcile on demand without changing the UoW's default config.

```python
import asyncio

from fennflow.reconciler import Reconciler, ReconcileStrategyEnum
from fennflow.uow import UowInspector


async def main():
    async with UOW() as uow:
        uow_inspector = UowInspector(uow=uow)
        reconcile = Reconciler(
            uow_fields=uow_inspector.get_repo_fields(),
            connector=uow.connector,
            backend=uow.backend,
            )
        await reconcile.reconcile(
            session_id=uow._session_id,
            batch_size=500,
            strategy=ReconcileStrategyEnum.REPLACE,
            )


if __name__ == "__main__":
    asyncio.run(main())
```

`UowInspector` introspects the UoW class and yields all declared `RepoField` instances. `Reconciler` then paginates
through each field's namespace in the file storage and syncs the backend according to the chosen strategy.

Note that manual reconciliation runs inside an open session. Any `PENDING` operations from the current session are not
affected — reconciliation only touches `UPLOADED` records in the persistent backend storage, not the session-local
operation buffer.
