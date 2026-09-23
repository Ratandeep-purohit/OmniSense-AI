"""Adapter registry with deterministic selection and no application execution authority."""
from .base import ApplicationAdapter, GenericWindowsAdapter
from ..application_identity.models import ApplicationIdentity

class ApplicationAdapterRegistry:
    def __init__(self, adapters: tuple[ApplicationAdapter,...]=()): self._adapters=adapters+(GenericWindowsAdapter(),)
    def select(self, identity: ApplicationIdentity) -> ApplicationAdapter:
        for adapter in self._adapters:
            if adapter.supports(identity): return adapter
        return self._adapters[-1]
