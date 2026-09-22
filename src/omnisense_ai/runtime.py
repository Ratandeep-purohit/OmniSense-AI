"""Application lifecycle and runtime state for Phase 0."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from threading import RLock

from .config import AppConfig
from .errors import LifecycleError


class RuntimeState(StrEnum):
    CREATED = "created"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class RuntimeSnapshot:
    state: RuntimeState
    environment: str
    generation: int


class ApplicationRuntime:
    """Small, deterministic lifecycle coordinator.

    Phase 0 owns lifecycle state only. It does not start capture, AI, OCR,
    automation, or any future-phase authority.
    """

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._state = RuntimeState.CREATED
        self._generation = 0
        self._lock = RLock()

    @property
    def state(self) -> RuntimeState:
        with self._lock:
            return self._state

    def snapshot(self) -> RuntimeSnapshot:
        with self._lock:
            return RuntimeSnapshot(
                state=self._state,
                environment=self._config.environment,
                generation=self._generation,
            )

    def start(self) -> RuntimeSnapshot:
        with self._lock:
            if self._state is RuntimeState.RUNNING:
                return self.snapshot()
            if self._state not in {RuntimeState.CREATED, RuntimeState.STOPPED}:
                raise LifecycleError(
                    f"Cannot start runtime from state '{self._state.value}'."
                )
            self._state = RuntimeState.STARTING
            self._generation += 1
            self._state = RuntimeState.RUNNING
            return self.snapshot()

    def stop(self) -> RuntimeSnapshot:
        with self._lock:
            if self._state is RuntimeState.STOPPED:
                return self.snapshot()
            if self._state not in {RuntimeState.RUNNING, RuntimeState.FAILED}:
                raise LifecycleError(
                    f"Cannot stop runtime from state '{self._state.value}'."
                )
            self._state = RuntimeState.STOPPING
            self._state = RuntimeState.STOPPED
            return self.snapshot()

    def fail(self) -> RuntimeSnapshot:
        with self._lock:
            self._state = RuntimeState.FAILED
            return self.snapshot()

    def restart(self) -> RuntimeSnapshot:
        with self._lock:
            if self._state is RuntimeState.RUNNING:
                self._state = RuntimeState.STOPPING
                self._state = RuntimeState.STOPPED
            elif self._state not in {RuntimeState.CREATED, RuntimeState.STOPPED, RuntimeState.FAILED}:
                raise LifecycleError(
                    f"Cannot restart runtime from state '{self._state.value}'."
                )
            self._state = RuntimeState.STARTING
            self._generation += 1
            self._state = RuntimeState.RUNNING
            return self.snapshot()
