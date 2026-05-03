from __future__ import annotations

from dataclasses import dataclass

from fennflow._operations.context.abstract import AbstractContext


@dataclass(slots=True)
class DeleteContext(AbstractContext, total=True):
    to_filepath: str
    to_namespace: str
