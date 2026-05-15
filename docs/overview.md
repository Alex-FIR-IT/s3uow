# Overview

FennFlow encapsulates all the logic of the Saga and SSOT (single source of truth) approaches, wrapping all file
operations in Pydantic models.

S3 has no concept of transactions.
A multi-step operation that fails halfway leaves storage in an unknown state.
FennFlow addresses this with two complementary patterns: SSOT ensures the backend always presents a consistent view of
what exists, and Saga ensures any partially executed sequence is fully compensated on failure. Together they guarantee
that from the end user's perspective, an operation either happened completely or not at all.

## SSOT: backend as a single source of truth

File storage (S3, etc.) is treated as a dumb byte store — it has no concept of sessions, pending operations, or
consistency guarantees. FennFlow introduces a **backend** as a metadata layer that sits above the file storage and
owns the authoritative view of what exists.

Before any read or write reaches the file storage, the backend is consulted first:

- `GET` operation only proceed to the connector if the backend has a record of the file. If the backend
  doesn't know about it, the file is considered non-existent — even if it physically lives in S3.
- `PUT` and `DELETE` operations are registered in the backend as `PENDING` before the connector is touched.

This separation means the backend can always answer "what exists right now?" consistently, regardless of what the file
storage contains at any given moment — including files left behind by crashed sessions or external processes.

## Saga: how operations reach consistency

FennFlow does not use distributed transactions or the Outbox pattern. The Outbox pattern requires a separate process to
relay messages, which adds infrastructure dependency.
Instead, FennFlow uses a Saga-like flow driven entirely by the backend.

Saga is a pattern for managing multi-step operations without distributed transactions. Each step is executed
independently and paired with a compensation action that can undo it. If any step fails, compensations are run in
reverse order to restore consistency.

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

### How write operation compensation works

Write operations that physically modify the file storage need a way to undo their effect on rollback. FennFlow handles
this by preserving enough state before executing the operation so that compensation can fully reverse it.

A `DELETE`, for example, does not immediately remove the file. Instead, on execute, the file is **copied to a temporary
path** inside the same storage:

```
tmp/session_{session_id}/operation_{operation_id}/{original_path}
```

The original file is then deleted. If rollback is needed, the compensation step copies the file back from `tmp/` to its
original path. If commit succeeds, the `tmp/` file is removed during finalize.

Temporary files live in the file storage itself, not in memory. This pattern applies to all write operations that
require compensation.

### Operation expiry

A pending operation record expires after 30 seconds. An expired pending record is treated as non-locking: another
session can write to the same path without waiting. This prevents abandoned operations (from crashed processes) from
blocking future writes indefinitely. A proper health-check mechanism is on
the [roadmap](https://github.com/users/Alex-FIR-IT/projects/2).

### Session isolation

A file uploaded by session A as `PENDING` is visible only to session A during that session. Other sessions see only
`UPLOADED` files. This means reads within an open UoW reflect the current session's own uncommitted writes, but never
another session's. This is similar to sqlalchemy sessions.