# Connectors

A connector performs the **actual I/O** against your file storage. Where the backend tracks what should exist, the
connector is what physically puts, gets, deletes, and lists objects.

Connectors are not called directly by user code. The UoW and repositories route all operations through the connector
internally.

## S3Connector

Backed by `aiobotocore`. Compatible with AWS S3 and any S3-compatible storage (MinIO, Selectel, etc.).

```python
from fennflow.connectors import S3ConnectorConfig


class UOW(UnitOfWork):
    config = ConfigDict(
        connector=S3ConnectorConfig()
```

If you omit credentials, the standard AWS credential chain is used (environment variables, `~/.aws/credentials`, IAM
roles, etc.).
For a quick start you can declare the following env vars in your .env file:

```ini
AWS_ACCESS_KEY_ID = ...
AWS_SECRET_ACCESS_KEY = ...
AWS_DEFAULT_REGION = ...
AWS_ENDPOINT_URL = ...
```

`S3ConnectorConfig.aiobotocore_config` accepts an `AioConfig` instance for advanced client tuning (timeouts, retries,
connection pool
size, etc.).

## InMemoryConnector

Stores files in a class-level dictionary within the process. Intended for tests and local development.

```python
from fennflow.connectors import InMemoryConnectorConfig


class UOW(UnitOfWork):
    config = ConfigDict(
        connector=InMemoryConnectorConfig(),
        )
```

Call `InMemoryConnector.drop_all()` between tests to reset connector state.

## Default config

If `config` is omitted entirely from a UoW subclass, backend and connector default to InMemoryBackend and S3Connector
accordingly.

## Implementing a custom connector

Subclass `AbstractConnector` and register it in `connector_registry`.

For available and planned connectors, see the [roadmap](https://github.com/users/Alex-FIR-IT/projects/2/views/2). If you
need a
connector that isn't there, [open an issue](https://github.com/Alex-FIR-IT/FennFlow/issues).
