from __future__ import annotations

from typing import TYPE_CHECKING

from fennflow.repositories.fields.base import RepoField, RepoType

from .base import RepoExtra

if TYPE_CHECKING:
    from fennflow._new_types import Namespace


class S3Extra(RepoExtra):
    """Configuration parameters for S3-backed repository fields."""

    bucket_name: Namespace  # alias for namespace


def S3RepoField(
    repo_cls: type[RepoType],
    bucket_name: Namespace,
) -> RepoField[RepoType]:
    """Create a RepoField configured for S3 storage.

    Args:
        repo_cls: The repository class to instantiate.
        bucket_name: alias for RepoField.namespace.

    Returns:
        A configured RepoField bound to the given repository class.

    **Example**::

        class UOW(UnitOfWork):
            user_files = S3RepoField(UserFiles, bucket_name="my-bucket")

    """
    return RepoField(
        repo_cls,
        namespace=bucket_name,
    )
