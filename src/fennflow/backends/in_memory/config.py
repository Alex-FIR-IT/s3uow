from fennflow.backends.abstract.config import AbstractBackendConfig


class InMemoryBackendConfig(AbstractBackendConfig):
    """Configuration for the in-memory backend.

    No configuration is required — the in-memory backend
    is zero-dependency.
    """
