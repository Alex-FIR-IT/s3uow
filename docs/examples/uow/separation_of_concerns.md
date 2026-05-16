```python
# 1. Define your repository with mixins
class CrudRepository(
    PutRepository,
    DeleteRepository,
    GetRepository,
    ListRepository,
    ):
    pass


class ReadOnlyRepository(
    GetRepository,
    ListRepository,
    ):
    pass


class UserFilesUOW(UnitOfWork):
    credentials = S3RepoField(CrudRepository, bucket_name="credentials")
    photos = S3RepoField(CrudRepository, bucket_name="photos")
    config = ConfigDict(
        backend=InMemoryBackendConfig(),
        connector=S3ConnectorConfig(),
        )


class BackupUOW(UnitOfWork):
    backup_files = S3RepoField(ReadOnlyRepository, bucket_name="backup_files")
    config = ConfigDict(
        backend=InMemoryBackendConfig(),
        connector=S3ConnectorConfig(),
        )

```