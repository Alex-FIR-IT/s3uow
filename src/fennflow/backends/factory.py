from typing import TYPE_CHECKING

from .registry import backend_registry

if TYPE_CHECKING:
    from fennflow.backends.abstract.base import AbstractBackend
    from fennflow.backends.types.config import BackendConfig


class BackendFactory:
    """Factory for creating backends from config."""

    @staticmethod
    def from_config(config: "BackendConfig") -> "AbstractBackend":

        backend_cls = backend_registry.get(config.__class__.__name__)
        if not backend_cls:
            raise ValueError(f"Unknown backend for : {type(config)=}")

        return backend_cls(config=config)
