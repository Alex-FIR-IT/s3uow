# PutRepository

Uploads one or more files to storage within the current Unit of Work session.
All uploads are tracked by the backend and compensated automatically on failure.

## Usage

```python
from fennflow.repositories import PutRepository


class UserFiles(PutRepository, ...):
    pass


async with UOW() as uow:
    await uow.user_files.at("user1/").put(file1, file2)
```

## Signature

```python
async def put(
        self,
        *files: BinaryMedia,
        **provider_extra
        ) -> None
```

### Arguments

| Argument           | Type          | Description                                      |
|--------------------|---------------|--------------------------------------------------|
| `*files`           | `BinaryMedia` | One or more media content objects to upload      |
| `**provider_extra` | `Any`         | Extra kwargs forwarded directly to the connector |

## Raises

| Exception                      | When                                                                              |
|--------------------------------|-----------------------------------------------------------------------------------|
| `RecordAlreadyExistsException` | A file with status="uploaded" and the same filepath already exists in the backend |

## Notes

- Files are uploaded concurrently via `asyncio.gather`
- If any upload fails, all operations in the session are compensated on `__aexit__`
- `filepath` is determined by `file.filename` joined with the current path set via `at()`

## Example

```python
from fennflow.files import TextContent, JsonContent
from fennflow.backends.abstract.exceptions import RecordAlreadyExistsException

async with UOW() as uow:
    file1 = TextContent.from_content("hello")
    file2 = JsonContent.from_content({"key": "value"})

    await uow.user_files.at("user1/").put(file1, file2)

    # raises RecordAlreadyExistsException
    try:
        await uow.user_files.at("user1/").put(file1)
    except RecordAlreadyExistsException:
        print("file already exists")
```