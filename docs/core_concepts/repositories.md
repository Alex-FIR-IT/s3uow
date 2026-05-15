# Repositories

Repositories are the interface through which user code interacts with file storage. They are declared as fields on a UoW
subclass and expose typed, Saga-tracked operations.

## Mixins

FennFlow uses a mixin pattern. You compose a repository class from the capabilities you need:

```python
from fennflow.repositories import (
    PutRepository,
    GetRepository,
    DeleteRepository,
    ListRepository,
    )


class CrudRepository(
    PutRepository,
    DeleteRepository,
    GetRepository,
    ListRepository,
    ):
    pass
```

Available mixins:

| Mixin              | Operation                            | Participates in Saga |
|--------------------|--------------------------------------|----------------------|
| `PutRepository`    | Upsert one or more files             | Yes                  |
| `GetRepository`    | Download one or more files           | No (read-only)       |
| `DeleteRepository` | Delete a file                        | Yes                  |
| `ListRepository`   | List files by prefix with pagination | No (read-only)       |
| `CreateRepository` | Upload one or more files             | Yes                  |

Read-only operations (such as `GetRepository` and `ListRepository`) consult the backend before touching storage. If the
backend has no record of a file, no network request is made.

## RepoField and S3RepoField

Attach a repository class to a UoW using a field descriptor:

```python
from fennflow.repositories import RepoField, S3RepoField


class UOW(UnitOfWork):
    # generic — namespace maps to whatever the connector uses as a bucket/prefix
    user_files = RepoField(CrudRepository, namespace="user-files")

    # S3-specific alias — bucket_name is just a named alias for namespace
    user_files = S3RepoField(CrudRepository, bucket_name="user-files")
```

`S3RepoField` is a convenience wrapper around `RepoField`. Functionally identical — it exists to make intent explicit
when working with S3.

The field is lazily initialized: the repository instance is created on first attribute access within a session.

## Path scoping with `.at()`

All repository mixins inherit `.at()` from `AtRepository`. It returns a new repository instance scoped to the given
path, without modifying the original:

```python
async with UOW() as uow:
    # scope to a subfolder
    storage = uow.user_files.at("user1/docs")
    await storage.put(file)

    # chain further
    await uow.user_files.at("user1").at("docs").put(file)
```

`.at()` calls are additive and composable. The path is normalized internally. The original field (`uow.user_files`) is
unchanged after `.at()`.

`.cwd` returns the current normalized path of a scoped repository instance.
