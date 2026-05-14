# Backends

A backend stores **operation metadata** — which files exist, their current status, and which session owns a pending
operation. It is the source of truth for FennFlow: if a file is not in the backend, it is invisible to the UoW
regardless of what the file storage contains.

Backends do not store file data. That is the connector's responsibility.

## Why a separate backend?

Raw file storage (S3, etc.) has no concept of pending operations, sessions, or compensation. The backend gives FennFlow
a consistent view of state that it can query, lock, and update independently of the storage. This is what makes the Saga
flow possible: the backend is always consulted before any storage operation, and its state is what commit and rollback
act on.

## InMemoryBackend

The default backend. State is kept in a class-level dictionary shared across all UoW instances within the same process.

```python
from fennflow.backends import InMemoryBackendConfig


class UOW(UnitOfWork):
    config = ConfigDict(
        backend=InMemoryBackendConfig(),
        )
```

`InMemoryBackendConfig` accepts an optional `scope` field (default `"fennflow_backend"`). Use different scopes when
running multiple UoW classes in the same process that point to different storage instances, to prevent their metadata
from merging.

```python
from fennflow.backends import InMemoryBackendConfig


class S3UOW(UnitOfWork):
    config = ConfigDict(
        backend=InMemoryBackendConfig(scope="s3_metadata"),
        )


class MinioUOW(UnitOfWork):
    config = ConfigDict(
        backend=InMemoryBackendConfig(scope="minio_metadata"),
        )
```

**Tradeoffs:**

- Zero infrastructure — no external service required.
- State is lost on process restart. The reconciler handles re-sync (see [Reconciler](reconciler.md)).
- Files uploaded during a crash before commit cannot be compensated after restart, since their pending records are gone.

`InMemoryBackend` is suitable for development, testing, and small deployments where process restarts are acceptable.

## Implementing a custom backend

Subclass `AbstractBackend` and register it in `backend_registry`.

For available and planned backends, see the [roadmap](https://github.com/users/Alex-FIR-IT/projects/2/views/2).
If you need a backend that isn't there, [open an issue](https://github.com/Alex-FIR-IT/FennFlow/issues).
