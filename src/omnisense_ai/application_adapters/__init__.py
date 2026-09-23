"""Application-specific behavior layered over generic Windows automation."""
from .base import ApplicationAdapter, GenericWindowsAdapter
from .registry import ApplicationAdapterRegistry
__all__=["ApplicationAdapter","GenericWindowsAdapter","ApplicationAdapterRegistry"]
