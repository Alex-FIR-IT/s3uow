<div align="center">
    <a href="https://github.com/Alex-FIR-IT/FennFlow">
    <picture>
      <img src="https://c438939f-e2e4-4a9c-a938-fc6e872413f4.selstorage.ru/github.png" alt="FennFlow">
    </picture>
  </a>
</div>
<div align="center">
  <h3>Atomic-like S3 Framework, the Pydantic way</h3>
</div>
<div align="center">
  <a href="https://github.com/Alex-FIR-IT/FennFlow/actions/workflows/coverage-report.yml"><img src="https://github.com/Alex-FIR-IT/FennFlow/actions/workflows/coverage-report.yml/badge.svg?branch=master" alt="CI"></a>
  <a href="https://app.codacy.com/gh/Alex-FIR-IT/FennFlow/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_coverage"><img src="https://app.codacy.com/project/badge/Coverage/3db23fc6c6f248f2926731b0bdf0d012" alt="Codacy Coverage"></a>
  <a href="https://github.com/users/Alex-FIR-IT/projects/2/views/2"><img src="https://img.shields.io/badge/Roadmap-green?logo=github" alt="Roadmap"></a>
  <a href="https://github.com/Alex-FIR-IT"><img src="https://img.shields.io/pypi/pyversions/fennflow?style=flat&logo=python&logoColor=white" alt="versions"></a>
  <a href="https://github.com/Alex-FIR-IT/fennflow/blob/master/LICENSE"><img src="https://img.shields.io/badge/license-MIT-brightgreen" alt="License: MIT"></a>
  <a href="https://github.com/Alex-FIR-IT/fennflow/commits/master/"><img src="https://img.shields.io/github/last-commit/Alex-FIR-IT/fennflow?logo=github" alt="Last Commit"></a>
  <a href="https://app.codacy.com/gh/Alex-FIR-IT/FennFlow/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade"><img src="https://app.codacy.com/project/badge/Grade/3db23fc6c6f248f2926731b0bdf0d012" alt="Codacy Grade"></a>
</div>

---

**Documentation**: [docs/README.md](https://github.com/Alex-FIR-IT/FennFlow/blob/master/docs/README.md)

---

### <em>FennFlow is a Python s3 framework designed to help you quickly, confidently, and painlessly manipulate files in your object storage implementing Saga-like compensation flow.</em>

## Why use FennFlow?

Working with aiobotocore often feels like handling raw bytes and dicts. `FennFlow` wraps S3 operations into a high-level
Unit of Work pattern, providing:

- **Atomic-like multistep operations** — if something fails, previous actions are automatically compensated (Saga
  Pattern).
- **Clean Architecture** — treat S3 as proper repositories using mixins (`PutRepository`, `GetRepository`, etc.).
- **Pydantic-powered models** — work with `TextContent`, `JsonContent`, `ImageContent` and others instead of raw bytes.

## Supported Connectors

| Connector           | Description                                  | Documentation                               |
|---------------------|----------------------------------------------|---------------------------------------------|
| AWS S3              | s3 compatible object storage via aiobotocore | [Quick start](docs/connectors/s3.md)        |
| In-Memory (default) | great for and tests and development          | [Quick start](docs/connectors/in-memory.md) |

## Supported Backends

FennFlow uses backend as a source of truth for your file storage.
No matter what your file storage contains, backend ensures your data is consistent.

| Backend             | Description                                         | Documenration                             |
|---------------------|-----------------------------------------------------|-------------------------------------------|
| In-Memory (default) | great for and tests, development and small projects | [Quick start](docs/backends/in-memory.md) |

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
from fennflow.files import BinaryContent, JsonContent, TextContent
from fennflow.repositories import (
    DeleteRepository,
    GetRepository,
    ListRepository,
    PutRepository,
    S3RepoField,
    )


# 1. Define your repository with mixins
class CrudRepository(
    PutRepository,
    DeleteRepository,
    GetRepository,
    ListRepository,
    ):
    pass


# 2. Set up your Unit of Work
class UOW(UnitOfWork):
    my_files = S3RepoField(CrudRepository, bucket_name="my_files")
    config = ConfigDict(
        backend=InMemoryBackendConfig(),
        connector=S3ConnectorConfig(),
        )


async def main():
    text_file = TextContent.from_content("Hello, world!")
    json_file = JsonContent.from_content([1, 2, 3])
    binary_file = BinaryContent(data=b"some bytes", media_type="text/plain")

    async with UOW() as uow:
        await uow.my_files.at("folder1").put(
            text_file,
            json_file,
            binary_file,
            )

        paths = await uow.my_files.at("folder1").list()
        print(paths)  # ListResponse[Filepath, ...]

        files = await uow.my_files.get(*paths)
        print(files)  # MediaResponse[TextContent, JsonContent, BinaryContent]


if __name__ == "__main__":
    asyncio.run(main())
```

## Next Steps

Read the [docs](https://github.com/Alex-FIR-IT/FennFlow/blob/master/docs/README.md) to learn more about working with
FennFlow.

