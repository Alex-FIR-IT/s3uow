# Unit of Work

`UnitOfWork` is the main entry point of FennFlow. Every file operation must go through it. It owns the session,
coordinates the backend and connector, and enforces the Saga compensation flow.

```python
async with UOW() as uow:
    await uow.user_files.at("user1/").put(file)
```

## Defining a UoW

Subclass `UnitOfWork`, declare your repositories as class-level fields, and set a `config`:

```python
from fennflow import ConfigDict, UnitOfWork
from fennflow.backends import InMemoryBackendConfig
from fennflow.connectors import S3ConnectorConfig
from fennflow.repositories import PutRepository, GetRepository, S3RepoField


class MyRepo(PutRepository, GetRepository):
    pass


class UOW(UnitOfWork):
    config = ConfigDict(
        backend=InMemoryBackendConfig(),
        connector=S3ConnectorConfig(...),
        )
    user_files = S3RepoField(MyRepo, bucket_name="my-bucket")
```

All fields declared on the class become repository instances scoped to the session on first access.

## Lifecycle

Opening a UoW with `async with` does three things in order:

1. Opens the backend and connector concurrently.
2. Runs the reconciler according to the ReconcileConfig (see [Reconciler](reconciler.md)).
3. Returns the UoW instance ready for operations.

On exit, the UoW either commits or rolls back, then closes both backend and connector.

## auto_commit

By default `auto_commit=True`. The UoW commits if the `async with` block exits cleanly, and rolls back if an exception
is raised.

Set `auto_commit=False` to control commit manually:

```python
async with UOW(auto_commit=False) as uow:
    await uow.user_files.at("user1/").put(file)
    await uow.commit() 
```

## Saga: how operations reach consistency

FennFlow does not use distributed transactions or the Outbox pattern. The Outbox pattern requires a separate process to
relay messages, which adds infrastructure dependency.
Instead, FennFlow uses a Saga-like flow driven entirely by the backend.

The **backend is the source of truth**. Whatever the backend says exists, exists — regardless of what the file storage
currently holds.

### Operation lifecycle

Every write operation goes through these steps:

```
register as PENDING in backend
        │
        ▼
execute against file storage
        │
   ┌────┴────┐
commit      rollback
   │            │
mark DONE   compensate in reverse order
```

**Commit path** (`uow.commit()`):

1. Fetch all `PENDING` operations from the backend.
2. Mark each one as successful in the backend and flush.
3. Finalize each operation (cleanup of temporary resources).

**Rollback path** (`uow.rollback()`):

1. Fetch all `PENDING` operations from the backend in reverse order.
2. For each operation, run its compensation against the file storage.
3. Mark compensated operations and flush.
4. Finalize.

Compensation logic is operation-specific. For instance:

- `PUT` compensation — deletes the uploaded file.
- `DELETE` compensation — restores the file from its temporary copy (see below).

### How DELETE compensation works

A `DELETE` does not immediately remove the file. Instead, on execute, the file is **copied to a temporary path** inside
the same storage:

```
tmp/session_{session_id}/operation_{operation_id}/{original_path}
```

The original file is then deleted. If rollback is needed, the compensation step copies the file back from `tmp/` to its
original path. If commit succeeds, the `tmp/` file is removed during finalize.

Temporary files live in the file storage itself, not in memory.

### Operation expiry

A pending operation record expires after 30 seconds. An expired pending record is treated as non-locking: another
session can write to the same path without waiting. This prevents abandoned operations (from crashed processes) from
blocking future writes indefinitely. A proper health-check mechanism is on
the [roadmap](https://github.com/users/Alex-FIR-IT/projects/2).

### Session isolation

A file uploaded by session A as `PENDING` is visible only to session A during that session. Other sessions see only
`UPLOADED` files. This means reads within an open UoW reflect the current session's own uncommitted writes, but never
another session's. This is similar to sqlalchemy sessions.
