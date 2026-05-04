from pydantic import TypeAdapter
from typing_extensions import TypedDict, Unpack

from fennflow.repositories.base import RepoExtra
from fennflow.repositories.fields.base import RepoField, RepoType


class S3Extra(RepoExtra):
    bucket_name: str  # alias for namespace


def S3RepoField(
    repo_cls: type[RepoType],
    **extra: Unpack[S3Extra],
) -> RepoField[RepoType]:
    adapter = TypeAdapter(S3Extra)
    result = adapter.validate_python(extra)
    result["namespace"] = result["bucket_name"]

    return RepoField(repo_cls, **result)
