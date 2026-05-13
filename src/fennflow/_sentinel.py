from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeGuard, TypeVar, Union

_T = TypeVar("_T")


# Sentinel class used until PEP 0661 is accepted


@dataclass(slots=True, frozen=True)
class NotGiven:
    """A sentinel singleton class used to distinguish omitted keyword arguments.

    Used to separate from those passed in with the value None (which may
    have different behavior).
    For example:

    ```py
    def get(timeout: Union[int, NotGiven, None] = NotGiven) -> Response: ...


    get(timeout=1)  # 1s timeout
    get(timeout=None)  # No timeout
    get()  # Default timeout behavior, which may not be statically known
    at the method definition.
    ```
    """

    def __bool__(self) -> Literal[False]:
        return False

    def __repr__(self) -> str:
        return "NOT_GIVEN"


NOT_GIVEN = NotGiven()


@dataclass(slots=True, frozen=True)
class Omit:
    """To explicitly omit something from being sent in a request, use `omit`.

    ```py
    # as the default `Content-Type` header is `application/json` that will be sent
    client.post("/upload/files", files={"file": b"my raw file content"})

    # you can't explicitly override the header as it has to be dynamically generated
    # to look something like:
    'multipart/form-data; boundary=0d8382fcf5f8c3be01ca2e11002d2983'
    client.post(..., headers={"Content-Type": "multipart/form-data"})

    # instead you can remove the default `application/json` header by passing omit
    client.post(..., headers={"Content-Type": omit})
    ```
    """

    def __bool__(self) -> Literal[False]:
        return False


OMIT = Omit()

Omittable = Union[_T, Omit]  # noqa: UP007


def is_given(obj: _T | NotGiven | Omit) -> TypeGuard[_T]:
    return not isinstance(obj, NotGiven) and not isinstance(obj, Omit)
