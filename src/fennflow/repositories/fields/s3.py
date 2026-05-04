from pydantic import TypeAdapter
from typing_extensions import Unpack

from fennflow.repositories.base import RepoExtra
from fennflow.repositories.fields.base import RepoField, RepoType


class S3Extra(RepoExtra):
    """Configuration parameters for S3-backed repository fields."""

    bucket_name: str  # alias for namespace


def S3RepoField(
    repo_cls: type[RepoType],
    **extra: Unpack[S3Extra],
) -> RepoField[RepoType]:
    """Create a RepoField configured for S3 storage.

    Args:
        repo_cls: The repository class to instantiate.
        **extra: S3-specific configuration. Requires ``bucket_name``.

    Returns:
        A configured RepoField bound to the given repository class.

    Example:
        class UOW(UnitOfWork):
            user_files = S3RepoField(UserFiles, bucket_name="my-bucket")

    """
    adapter = TypeAdapter(S3Extra)
    result = adapter.validate_python(extra)
    result["namespace"] = result["bucket_name"]

    return RepoField(repo_cls, **result)
