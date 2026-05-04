# In-Memory Backend

Stores saga metadata in process memory. Zero dependencies, zero infrastructure.
Intended for testing, development, and small projects.

## Installation

```bash
uv add fennflow
```

or

```bash
pip install fennflow
```

## Configuration

```python
from fennflow.backends import InMemoryBackendConfig

config = InMemoryBackendConfig()
```

## Quick Start

```python
import asyncio

from fennflow import ConfigDict, UnitOfWork
from fennflow.backends import InMemoryBackendConfig
from fennflow.connectors import InMemoryConnectorConfig
from fennflow.files import TextContent
from fennflow.repositories import DeleteRepository, GetRepository, PutRepository
from fennflow.repositories.fields.base import RepoField


class UserFiles(
    PutRepository,
    DeleteRepository,
    GetRepository,
    ):
    pass


class UOW(UnitOfWork):
    user_files = RepoField(UserFiles, namespace="user-files")
    config = ConfigDict(
        backend=InMemoryBackendConfig(),
        connector=InMemoryConnectorConfig(),
        )


async def main():
    async with UOW() as uow:
        file = TextContent.from_content("Hello, World!")

        await uow.user_files.at("user1/").put(file)

        response = await uow.user_files.at("user1/").get(file.filename)
        file = response[0]
        print(file.content)  # "Hello, World!"

        await uow.user_files.at("user1/").delete(file.filename)


if __name__ == "__main__":
    asyncio.run(main())
```

(This example is complete, it can be run “as is”, assuming you’ve installed the fennflow package)

## Limitations

- Saga metadata is lost on process restart
- Operations interrupted by a crash cannot be compensated
- Use `InMemoryBackend.drop_all()` between tests to reset state
- For production workloads it's recommended to consider using Redis or SQLAlchemy backend instead 