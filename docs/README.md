# FennFlow Documentation

Welcome to the FennFlow documentation.

## Getting Started

- [Quick Start](../README.md#quick-start)
- [Connectors](connectors/README.md)
- [Backends](backends/README.md)
- [Repositories](repositories/README.md)

## Connectors

| Connector | Config Class              | Docs                                      |
|-----------|---------------------------|-------------------------------------------|
| AWS S3    | `S3ConnectorConfig`       | [📖 Quick Start](connectors/s3.md)        |
| In-Memory | `InMemoryConnectorConfig` | [📖 Quick Start](connectors/in-memory.md) |

## Backends

| Backend             | Config Class            | Docs                                    |
|---------------------|-------------------------|-----------------------------------------|
| In-Memory (default) | `InMemoryBackendConfig` | [📖 Quick Start](backends/in-memory.md) |

## Repositories

| Repository         | Method     | Description                 | Docs                              |
|--------------------|------------|-----------------------------|-----------------------------------|
| `PutRepository`    | `put()`    | Upload files to storage     | [📖 Docs](repositories/put.md)    |
| `GetRepository`    | `get()`    | Retrieve files from storage | [📖 Docs](repositories/get.md)    |
| `DeleteRepository` | `delete()` | Delete files from storage   | [📖 Docs](repositories/delete.md) |

## Working with Responses

All read operations return a `MediaResponse` object.

### Accessing media

```python
response = await uow.user_files.at("user1/").get("file.txt", "image.png")

# iterate
for item in response:
    print(item.data)

# index
first = response[0]

# count
print(len(response))
```

### Typed properties

```python
response.texts  # tuple[TextContent, ...]
response.images  # tuple[ImageContent, ...]
response.videos  # tuple[VideoContent, ...]
response.audios  # tuple[AudioContent, ...]
response.pdfs  # tuple[PdfContent, ...]
```

### Filtering

```python
# by type
images = response.filter(ImageContent)
text_and_json = response.filter(TextContent, JsonContent)

# by MIME type
texts = response.filter_by_media_type("text/plain", "application/json")
```

### Combining responses

```python
combined = MediaResponse.join([response1, response2])
```