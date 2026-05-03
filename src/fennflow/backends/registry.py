from .in_memory import InMemoryBackend, InMemoryBackendConfig

backend_registry = {
    InMemoryBackendConfig.__name__: InMemoryBackend,
}
