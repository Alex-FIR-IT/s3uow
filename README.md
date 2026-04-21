# FennFlow  &middot; [![License: MIT](https://img.shields.io/badge/license-MIT-brightgreen)](https://github.com/Alex-FIR-IT/fennflow/blob/master/LICENSE) [![Static Badge](https://img.shields.io/badge/Roadmap-green?logo=github)](https://github.com/users/Alex-FIR-IT/projects/2/views/2) [![last commit](https://img.shields.io/github/last-commit/Alex-FIR-IT/fennflow?logo=github)](https://github.com/Alex-FIR-IT/fennflow/commits/master/) [![Codacy Badge](https://app.codacy.com/project/badge/Grade/3db23fc6c6f248f2926731b0bdf0d012)](https://app.codacy.com/gh/Alex-FIR-IT/FennFlow/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)


### <em>FennFlow is a Python s3 framework designed to help you quickly, confidently, and painlessly manipulate files in your object storage implementing Saga-like compensation flow.</em>

> ⚠️ Project Status: Experimental / Work in Progress  
> This library is in early development (Alpha). The API is subject to change. **NOT READY** for production use yet.

## Why use FennFlow?

Working with aiobotocore often feels like handling raw bytes and dicts. `FennFlow` wraps S3 operations into a high-level Unit of Work pattern, providing:
- **Atomic-like multi-step operations** — if something fails, previous actions are automatically compensated (Saga Pattern).
- **Clean Architecture** — treat S3 as proper repositories using mixins (`PutRepository`, `GetRepository`, etc.).
- **Pydantic-powered models** — work with `TextContent`, `JsonContent`, `ImageContent` and others instead of raw bytes.


### Backend Comparison

FennFlow supports multiple backends for saga metadata and locking, just like Celery.

- **In-Memory** — default, great for and tests and development
- **Redis** — balanced choice for most production workloads  
- **SQLAlchemy** — maximum durability using your existing database (via SQLAlchemy). Just pass your DB URL — FennFlow handles the rest.


| Parameter       | Raw aiobotocore                                      | In-Memory (default)                                      | Redis                                                    | SQLAlchemy                                  |
|-----------------|------------------------------------------------------|----------------------------------------------------------|----------------------------------------------------------|----------------------------------------------------------|
| **Consistency** | 🟡 Eventual at best<br>No link between file and metadata | ✅ **Always consistent**<br>While the process is alive   | ✅ **Always consistent**<br>Survives worker crashes      | ✅ **Highest**<br>Strong ACID guarantees                 |
| **Reliability** | 🟡 Medium<br>Errors often leave orphaned files       | 🟡 Medium<br>Data is lost on process restart             | ✅ **High**<br>Survives restarts, protects against duplicates | ✅ **Highest**<br>Survives crashes, power loss, and network issues |
| **Latency**     | ✅ Lowest<br>Pure S3 network overhead                | ✅ **Lowest**<br>Minimal in-process overhead             | 🟡 Medium<br>Network round-trip per saga step            | 🟡 High<br>Additional SQL transaction + disk overhead    |
| **Complexity**  | ❌ None (raw code as you like)                       | ✅ **Lowest**<br>No extra infrastructure required        | 🟡 Medium<br>Just provide Redis connection URL           | 🟡 Medium<br>Provide your DB connection string (library handles tables) |
## Quick Start

Here's a minimal example of FennFlow:
```python3
import asyncio
from fennflow import UnitOfWork, ConfigDict
from fennflow.repositories import (
    PutRepository, DeletedRepository, GetRepository,
    GeneratePresignedURLRepository
)
from fennflow.files import TextContent

# 1. Define your scoped repository with Mixins
class UserFiles(
    PutRepository,
    DeletedRepository,
    GetRepository,
    GeneratePresignedURLRepository,
):
    BUCKET_NAME = "user-files"

# 2. Setup your Unit of Work
class UOW(UnitOfWork):
    user_files = UserFiles
    config = ConfigDict(storage='in-memory')

async def main():
    async with UOW() as uow:
        file1 = TextContent.from_content("Hello, World!")
        file2 = TextContent.from_content("Hello, World2!")

        # Put files with path scoping
        await uow.user_files.at("user1/").put(file1, file2)

        storage = uow.user_files.at("user1/")

        response1 = await storage.generate_presigned_url(file1.filename)
        response2 = await storage.get(file2.filename)
        print(response2.content)  # "Hello, World2!"

        await storage.delete(file1.filename)

if __name__ == "__main__":
    asyncio.run(main())
```

