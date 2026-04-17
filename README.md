# s3uow  &middot; ![Static Badge](https://img.shields.io/badge/license-MIT-brightgreen?link=https%3A%2F%2Fgithub.com%2FAlex-FIR-IT%2FWireGuard-Config-Maker%3Ftab%3DMIT-1-ov-file)

The Type-Safe Unit of Work for S3. Simplify your cloud storage logic with Pydantic-powered models and atomic transaction-like operations.

> ⚠️ Project Status: Experimental / Work in Progress  
> This library is in early development (Alpha). The API is subject to change. Not ready for production use yet.




## Overview

Working with aiobotocore often feels like handling raw bytes and dicts. `s3uow` wraps S3 operations into a high-level Unit of Work pattern, providing:
- Type Safety: Use Pydantic models for different file types (Texts, Images, JSON, Video, etc.).
- Atomic-ish Operations: Manage multiple S3 actions in a single session with a "Best Effort" rollback mechanism.
- Clean Architecture: Decouple your business logic from infrastructure using repositories and mixins.

## Quick Start

```python3
import asyncio
from s3_uow import UnitOfWork, ConfigDict
from s3_uow.repositories import (
    PutRepository, DeletedRepository, GetRepository, 
    GeneratePresignedURLRepository, PutStreamRepository
)
from s3_uow.files import TextContent

# 1. Define your scoped repository with Mixins
class UserFiles(
    PutRepository,
    DeletedRepository,
    GetRepository,
    GeneratePresignedURLRepository,
    PutStreamRepository,
):
    BUCKET_NAME = "user-files"

# 2. Setup your Unit of Work
class UOW(UnitOfWork):
    user_files = UserFiles
    config = ConfigDict(storage='in-memory')

async def main():
    
    async with UOW(
            # auto_commit=True, # Use auto_commit=True for auto commit after exiting the context. True by default.
            # auto_commit_per_action=False, # Use auto_commit_per_action=True for auto commit after exiting the context. False by default
    ) as uow:
        file1 = TextContent.from_text("Hello, World!")
        file2 = TextContent.from_text("Hello, World2!")

        # Put files with path scoping
        await uow.user_files.at("user1/").put(file1)
        
        # Scoped storage for multiple operations
        storage = uow.user_files.at("user1/")

        # Type-safe responses (MediaResponse[UrlContent])
        response1 = await storage.generate_presigned_url(file1.filename)
        
        # Fetch with content casting (MediaResponse[TextContent])
        response2 = await storage.get(file2.filename)
        print(response2.content) # "Hello, World2!"
       
        await storage.delete(file1.filename)

if __name__ == "__main__":
    asyncio.run(main())
```

## Consistency & Saga Pattern
`s3uow` implements a Saga-like compensation logic. While S3 doesn't support native ACID transactions, s3uow tracks your actions during a session. If an operation fails, it attempts to "undo" previous actions (e.g., deleting uploaded files) to keep your storage clean.
