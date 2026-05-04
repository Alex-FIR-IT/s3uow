from __future__ import annotations

from functools import cache
from typing import Any

from pydantic import ValidationError

from fennflow.files.media.binary_content import BinaryContent
from fennflow.files.media.url_content import UrlContent
from fennflow.files.registry import content_registry
from fennflow.files.types import BinaryMedia


class ContentFactory:
    """Factory for creating media content instances from raw data.

    Resolves the appropriate content class from the registry based on
    MIME type, falling back to ``BinaryContent`` for unknown types.

    Example:
        content = ContentFactory.from_bytes("text/plain", b"Hello, World!")
        url = ContentFactory.from_url("https://example.com/file.txt")
    """

    @staticmethod
    @cache
    def _get_prefixes() -> list[str]:
        """Return registry prefixes sorted by length descending for match resolution."""
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
        """Create a media content instance from raw bytes.

        Resolves the content class from the registry by exact MIME type match,
        then by prefix match, falling back to ``BinaryContent`` if no match is found.

        Args:
            media_type: The MIME type of the content (e.g. ``"text/plain"``).
            data: The raw bytes to wrap.
            **kwargs: Additional fields passed to the content model.

        Returns:
            A media content instance appropriate for the given MIME type.

        Raises:
            TypeError: If ``data`` is not bytes.
            ValueError: If the resolved content class fails validation.
        """
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
        media_type: str = "application/octet-stream",
        **kwargs: Any,
    ) -> UrlContent:
        """Create a ``UrlContent`` instance from a URL string.

        Args:
            url: The URL string to wrap.
            media_type: The MIME type of the resource.
                Defaults to ``"application/octet-stream"``.
            **kwargs: Additional fields passed to the content model.

        Returns:
            A ``UrlContent`` instance wrapping the given URL.

        Raises:
            ValueError: If the URL fails validation.
        """
        payload = {
            "data": url,
            "media_type": media_type,
            **kwargs,
        }
        try:
            return UrlContent.model_validate(payload)
        except ValidationError as exc:
            raise ValueError(f"Failed to create UrlContent for {url=}") from exc
