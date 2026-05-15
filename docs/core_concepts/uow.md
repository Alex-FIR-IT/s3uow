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
from fennflow.repositories import CreateRepository, GetRepository, S3RepoField


class MyRepo(CreateRepository, GetRepository):
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
