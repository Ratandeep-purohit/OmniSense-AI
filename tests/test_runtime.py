from omnisense_ai.config import load_config
from omnisense_ai.runtime import ApplicationRuntime, RuntimeState


def test_runtime_starts_and_stops_deterministically() -> None:
    runtime = ApplicationRuntime(load_config({}))

    assert runtime.state is RuntimeState.CREATED
    started = runtime.start()
    assert started.state is RuntimeState.RUNNING
    assert started.generation == 1

    assert runtime.start().generation == 1
    stopped = runtime.stop()
    assert stopped.state is RuntimeState.STOPPED

    restarted = runtime.restart()
    assert restarted.state is RuntimeState.RUNNING
    assert restarted.generation == 2


def test_failed_runtime_can_be_stopped_and_restarted() -> None:
    runtime = ApplicationRuntime(load_config({}))
    runtime.start()
    failed = runtime.fail()

    assert failed.state is RuntimeState.FAILED
    assert runtime.stop().state is RuntimeState.STOPPED
    assert runtime.restart().state is RuntimeState.RUNNING
