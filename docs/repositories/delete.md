# DeleteRepository

Deletes a file from storage within the current Unit of Work session.

## Usage

```python
from fennflow.repositories import DeleteRepository


class UserFiles(DeleteRepository, ...):
    pass


async with UOW() as uow:
    deleted = await uow.user_files.at("user1/").delete("file.txt")
```

## Signature

```python
async def delete(
        self,
        path: str,
        **provider_extra
        ) -> bool
```

### Arguments

| Argument           | Type  | Description                                      |
|--------------------|-------|--------------------------------------------------|
| `path`             | `str` | Filename to delete relative to the current path  |
| `**provider_extra` | `Any` | Extra kwargs forwarded directly to the connector |

## Returns

| Result  | When                                               |
|---------|----------------------------------------------------|
| `True`  | Operation found in backend and deletion successful |
| `False` | Operation not found in backend                     |

## Notes

- Deletion is tracked by the backend and compensated automatically on failure
- If the file does not exist in the backend, `False` is returned and no connector call is made
- The actual deletion from storage happens within the UoW session

## Example

```python
async with UOW() as uow:
    deleted = await uow.user_files.at("user1/").delete("file.txt")

    if deleted:
        print("file deleted")
    else:
        print("file not found in backend")
```