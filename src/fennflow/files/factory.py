from __future__ import annotations

from functools import cache
from typing import Any

from pydantic import ValidationError

from fennflow.files.media.binary_content import BinaryContent
from fennflow.files.media.url_content import UrlContent
from fennflow.files.registry import content_registry
from fennflow.files.types import BinaryMedia


class ContentFactory:
    @staticmethod
    @cache
    def _get_prefixes() -> list[str]:
        return sorted(
            (p for p in content_registry if p.endswith("/")),
            key=len,
            reverse=True,
        )

    @classmethod
    def from_bytes(
        cls,
        media_type: str,
        data: bytes,
        **kwargs: Any,
    ) -> BinaryMedia:

        if not isinstance(data, bytes):
            raise TypeError(f"Factory expected bytes, got {type(data)=} instead.")

        payload = {
            "media_type": media_type,
            "data": data,
            **kwargs,
        }

        if media_type in content_registry:
            content_cls = content_registry[media_type]
        else:
            for prefix in cls._get_prefixes():
                if media_type.startswith(prefix):
                    content_cls = content_registry[prefix]
                    break
            else:
                content_cls = BinaryContent

        try:
            return content_cls.model_validate(payload)
        except ValidationError as exc:
            raise ValueError(
                f"Failed to validate {content_cls.__name__=} for {media_type=}"
            ) from exc

    @staticmethod
    def from_url(
        url: str,
        media_type: str | None = None,
        **kwargs: Any,
    ) -> UrlContent:
        payload = {
            "data": url,
            "media_type": media_type or "application/octet-stream",
            **kwargs,
        }
        try:
            return UrlContent.model_validate(payload)
        except ValidationError as exc:
            raise ValueError(f"Failed to create UrlContent for {url=}") from exc
