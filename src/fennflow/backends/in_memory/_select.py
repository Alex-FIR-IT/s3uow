from __future__ import annotations

import itertools
from typing import TYPE_CHECKING
from uuid import UUID

from typing_extensions import Unpack

from fennflow._datetime import now
from fennflow._operations.enums import OperationStatusEnum, OperationTypeEnum
from fennflow._sentinel import OMIT
from fennflow.backends.abstract.annotations import SelectParams
from fennflow.backends.responses import OperationPage

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable

    from fennflow._operations.dto import OperationRecord


class SelectOperation:
    def __init__(self, **kwargs: Unpack[SelectParams]):
        self.kwargs: SelectParams = kwargs
        self.kwargs.setdefault("limit", 1000)
        self.current_datetime = now()

        for key in SelectParams.__annotations__:
            self.kwargs.setdefault(key, OMIT)  # type: ignore[misc]

    @property
    def predicates(self):
        return (
            lambda record: (
                self.kwargs["path"] is OMIT or record.filepath == self.kwargs["path"]
            ),
            lambda record: (
                self.kwargs["prefix"] is OMIT
                or record.filepath.startswith(self.kwargs["prefix"])
            ),
            lambda record: (
                self.kwargs["status"] is OMIT or record.status == self.kwargs["status"]
            ),
            lambda record: (
                self.kwargs["media_type"] is OMIT
                or record.media_type == self.kwargs["media_type"]
            ),
            lambda record: (
                self.kwargs["session_id"] is OMIT
                or record.session_id == self.kwargs["session_id"]
            ),
            lambda record: (
                self.kwargs["operation_id"] is OMIT
                or record.operation_id == self.kwargs["operation_id"]
            ),
            lambda record: (
                self.kwargs["is_expired"] is OMIT
                or (record.expired_at <= self.current_datetime)
                == self.kwargs["is_expired"]
            ),
            lambda record: (
                self.kwargs["visible_for_session_id"] is OMIT
                or record.status == OperationStatusEnum.UPLOADED
                or (
                    record.status == OperationStatusEnum.PENDING
                    and record.session_id == self.kwargs["visible_for_session_id"]
                    and record.operation_type == OperationTypeEnum.PUT
                )
            ),
        )

    def sort_and_filter(
        self,
        all_records: Iterable[OperationRecord],
    ) -> Generator[OperationRecord, None, None]:

        continuation_token = self.kwargs["continuation_token"]

        if continuation_token:
            all_sorted = sorted(all_records, key=lambda r: r.created_at)
            cursor = UUID(continuation_token)
            after_cursor = itertools.dropwhile(
                lambda r: r.operation_id != cursor,
                all_sorted,
            )
            filtered_results = (
                record
                for record in after_cursor
                if all(p(record) for p in self.predicates)
            )
        else:
            sorted_records = sorted(
                (
                    record
                    for record in all_records
                    if all(p(record) for p in self.predicates)
                ),
                key=lambda r: r.created_at,
            )
            filtered_results = (record for record in sorted_records)

        return filtered_results

    def apply_limit(
        self, filtered_results: Iterable[OperationRecord]
    ) -> tuple[OperationRecord, ...]:
        return tuple(itertools.islice(filtered_results, self.kwargs["limit"]))

    def get_continuation_token(
        self, filtered_results: Generator[OperationRecord, None, None]
    ) -> str | None:
        next_item = next(filtered_results, None)
        next_token = str(next_item.operation_id) if next_item else None
        return next_token

    def select(self, record: Iterable[OperationRecord]) -> OperationPage:
        filtered_results = self.sort_and_filter(record)

        results = self.apply_limit(filtered_results)
        next_token = self.get_continuation_token(filtered_results)
        return OperationPage(
            operations=results,
            continuation_token=next_token,
        )
