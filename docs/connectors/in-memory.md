# In-Memory Connector

Stores files in process memory. Zero dependencies, zero infrastructure.
Intended for testing and development.

## Installation

```bash
uv add fennflow
```

or

```bash
pip install fennflow
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

## Notes

- Storage is shared across all instances within the same process
- All data is lost on process restart
- Use `InMemoryConnector.drop_all()` between tests to reset state
- Not recommended for production use