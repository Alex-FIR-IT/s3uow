# GetRepository

Retrieves one or more files from storage.

## Usage

```python
from fennflow.repositories import GetRepository


class UserFiles(GetRepository, ...):
    pass


async with UOW() as uow:
    response = await uow.user_files.at("user1/").get("file.txt")
    print(response.media[0].content)
```

## Signature

```python
async def get(
        self,
        *paths: str,
        **provider_extra
        ) -> MediaResponse
```

### Arguments

| Argument           | Type  | Description                                      |
|--------------------|-------|--------------------------------------------------|
| `*paths`           | `str` | One or more filenames to retrieve                |
| `**provider_extra` | `Any` | Extra kwargs forwarded directly to the connector |

## Returns

Always returns a `MediaResponse` — never raises on missing files.

| Result                       | When                    |
|------------------------------|-------------------------|
| `MediaResponse(media=(...))` | One or more files found |
| `MediaResponse()`            | File not found          |

## Notes

- Multiple files are fetched concurrently via `asyncio.gather`
- Missing files are silently omitted from the response
- Use properties`response.texts`, `response.images` and others for simple filter
- Use `response.filter(TextContent, ImageContent)` for multiple filter by content type
- Use `response.filter_by_media_type("text/plain", "images/png")` for multiple filter by MIME type

## Example

```python
async with UOW() as uow:
    # single file
    response = await uow.user_files.at("user1/").get("file.txt")

    if response:
        print(response.media[0].content)

    # multiple files — missing ones silently omitted
    response = await uow.user_files.at("user1/").get("file1.txt", "file2.txt")
    print(len(response))  # 0, 1, or 2 depending on what exists
```