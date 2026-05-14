# Files

FennFlow wraps raw bytes in typed content models instead of passing `bytes` and `dict` directly. Every file you put into
or get from storage is represented as one of these models.

All **binary** content types inherit from `BinaryContent`, which itself inherits from `BaseContent` (a Pydantic model).

## Content types

| Class             | Media type         | Notes                                                                      |
|-------------------|--------------------|----------------------------------------------------------------------------|
| `BinaryContent`   | any                | Base class. Use when no specific type fits                                 |
| `TextContent`     | `text/plain`       | Stores text as UTF-8 bytes internally. `.content` returns `str`            |
| `JsonContent`     | `application/json` | Stores JSON as UTF-8 bytes. `.content` returns the parsed Python object    |
| `ImageContent`    | `image/*`          | Extends `BinaryContent` with optional `width` and `height` fields          |
| `AudioContent`    | `audio/*`          | Extends `BinaryContent` with optional `duration` field                     |
| `VideoContent`    | `video/*`          | Extends `BinaryContent` with optional `duration`, `width`, `height` fields |
| `DocumentContent` | any document type  | Thin subclass of `BinaryContent`                                           |

There is also a model representing url files:

| Class        | Media type | Notes                                                 |
|--------------|------------|-------------------------------------------------------|
| `UrlContent` | any        | Stores a URL string instead of bytes. `data` is `str` |

## Creating content

`TextContent` and `JsonContent` expose a `from_content()` classmethod as the primary constructor:

```python
from fennflow.files import TextContent, JsonContent, BinaryContent, ImageContent, ContentFactory

text = TextContent.from_content("Hello, world!")
json_file = JsonContent.from_content({"key": "value"})
json_list = JsonContent.from_content([1, 2, 3])

# BinaryContent requires explicit media_type
binary = BinaryContent(data=b"...", media_type="application/octet-stream")

# Optional metadata fields
image = ImageContent(data=img_bytes, media_type="image/png", width=800, height=600)

# ContentFactory can be used to get specific class of content
file: TextContent = ContentFactory.from_bytes(
    media_type="text/plain",
    data=file_bytes,
    **metadata,
    ),

```

## Filename and media type resolution

Both `filename` and `media_type` are optional at construction time. FennFlow resolves them:

- If only `media_type` is given: filename is generated as the SHA-256 hash of the data, with the extension guessed from
  the media type.
- If only `filename` is given: media type is guessed from the extension via `mimetypes`.
- If both are omitted: raises `FileNameAndMediaTypeBothNoneException`.
- If the filename has no extension: the extension is guessed from the media type and appended.

A warning is logged if the file extension and media type do not agree.

## Extra metadata

Any keyword arguments not matching declared fields are collected into `extra_metadata: dict[str, str]`. This metadata is
forwarded to the connector (e.g. stored as S3 object metadata).

## ContentFactory

When FennFlow retrieves a file from storage, it reconstructs the appropriate content type using
`ContentFactory.from_bytes()`. The factory resolves the class from a registry by MIME type match falling back to
`BinaryContent` for unknown types.

You can register custom content types in `content_registry` to have them returned automatically on `get`.
