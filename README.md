# FennFlow &middot; [![License: MIT](https://img.shields.io/badge/license-MIT-brightgreen)](https://github.com/Alex-FIR-IT/fennflow/blob/master/LICENSE) [![Static Badge](https://img.shields.io/badge/Roadmap-green?logo=github)](https://github.com/users/Alex-FIR-IT/projects/2/views/2) [![last commit](https://img.shields.io/github/last-commit/Alex-FIR-IT/fennflow?logo=github)](https://github.com/Alex-FIR-IT/fennflow/commits/master/) [![Codacy Badge](https://app.codacy.com/project/badge/Grade/3db23fc6c6f248f2926731b0bdf0d012)](https://app.codacy.com/gh/Alex-FIR-IT/FennFlow/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade) [![Codacy Badge](https://app.codacy.com/project/badge/Coverage/3db23fc6c6f248f2926731b0bdf0d012)](https://app.codacy.com/gh/Alex-FIR-IT/FennFlow/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_coverage) [![Tests & Coverage](https://github.com/Alex-FIR-IT/FennFlow/actions/workflows/coverage-report.yml/badge.svg?branch=master)](https://github.com/Alex-FIR-IT/FennFlow/actions/workflows/coverage-report.yml)

### <em>FennFlow is a Python s3 framework designed to help you quickly, confidently, and painlessly manipulate files in your object storage implementing Saga-like compensation flow.</em>

> ⚠️ Project Status: Experimental / Work in Progress  
> This library is in early development (Alpha). The API is subject to change. **NOT READY** for production use yet.

## Why use FennFlow?

Working with aiobotocore often feels like handling raw bytes and dicts. `FennFlow` wraps S3 operations into a high-level
Unit of Work pattern, providing:

- **Atomic-like multi-step operations** — if something fails, previous actions are automatically compensated (Saga
  Pattern).
- **Clean Architecture** — treat S3 as proper repositories using mixins (`PutRepository`, `GetRepository`, etc.).
- **Pydantic-powered models** — work with `TextContent`, `JsonContent`, `ImageContent` and others instead of raw bytes.

## Supported Connectors

| Connector | Config Class              | Documentation                               |
|-----------|---------------------------|---------------------------------------------|
| AWS S3    | `S3ConnectorConfig`       | [Quick start](docs/connectors/s3.md)        |
| In-Memory | `InMemoryConnectorConfig` | [Quick start](docs/connectors/in-memory.md) |

## Supported Backends

FennFlow supports multiple backends for saga metadata and locking, just like Celery.

| Backend             | Config Class            | Description                                         | Documenration                             |
|---------------------|-------------------------|-----------------------------------------------------|-------------------------------------------|
| In-Memory (default) | `InMemoryBackendConfig` | great for and tests, development and small projects | [Quick start](docs/backends/in-memory.md) |

### Backend Comparison

|                    | Raw aiobotocore                                   | In-Memory                                                                                     |
|--------------------|---------------------------------------------------|-----------------------------------------------------------------------------------------------|
| **Consistency**    | 🔴 None<br>No link between files and metadata     | 🟡 Medium<br>Consistent within process lifetime, lost on crash                                | 
| **Compensation**   | 🔴 None<br>Orphaned files on failure              | 🟡 Medium<br>Automatic within process, orphaned files possible on crash                       | 
| **Reliability**    | 🔴 Low<br>Failures leave storage in unknown state | 🟡 Medium<br>Syncs with storage on restart, files uploaded during crash cannot be compensated | 
| **Latency**        | ✅ Lowest<br>Pure S3 network overhead only         | ✅ Lowest<br>Minimal in-process overhead                                                       | 
| **Infrastructure** | ✅ None                                            | ✅ None                                                                                        |
| **Memory usage**   | ✅ None                                            | 🟡 Stores file metadata in-process                                                            |

## Quick Start

Here's a minimal example of FennFlow:

```python3
import asyncio

from fennflow import ConfigDict, UnitOfWork
from fennflow.backends import InMemoryBackendConfig
from fennflow.connectors import S3ConnectorConfig
from fennflow.files import TextContent
from fennflow.repositories import DeleteRepository, GetRepository, PutRepository
from fennflow.repositories import S3RepoField


# 1. Define your repository with mixins
class UserFiles(
    PutRepository,
    DeleteRepository,
    GetRepository,
    ):
    pass


# 2. Set up your Unit of Work
class UOW(UnitOfWork):
    user_files = S3RepoField(UserFiles, bucket_name="user-files")
    config = ConfigDict(
        backend=InMemoryBackendConfig(),
        connector=S3ConnectorConfig(),
        )


async def main():
    # Auto-commit on success, auto-rollback with compensation on failure
    async with UOW() as uow:
        file1 = TextContent.from_content("Hello, World!")
        file2 = TextContent.from_content("Hello, World2!")

        # Upload files scoped to a path
        await uow.user_files.at("user1/").put(file1, file2)

        # Get a file
        response = await uow.user_files.at("user1/").get(file2.filename)
        print(response.media[0].content)  # "Hello, World2!"

        # Delete a file
        await uow.user_files.at("user1/").delete(file1.filename)


if __name__ == "__main__":
    asyncio.run(main())
```

## Next Steps

Read the [docs](docs/README.md) to learn more about working with FennFlow.

