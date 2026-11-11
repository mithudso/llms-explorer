"""Research process ownership survives cancellation of its asyncio waiter."""

import asyncio
import os
import signal
import stat
import sys

import pytest

from explorer_api import research


@pytest.fixture
def recorded_states(monkeypatch):
    states = []

    async def record(*args, **kwargs):
        states.append(kwargs)

    monkeypatch.setattr(research, "_set", record)
    monkeypatch.setattr(research, "_PROCS", set())
    return states


async def test_cancelled_run_kills_and_reaps_its_process(tmp_path, monkeypatch):
    async def record(*args, **kwargs):
        pass

    monkeypatch.setattr(research, "_set", record)
    monkeypatch.setattr(research, "_PROCS", set())
    task = asyncio.create_task(research.run(
        None, "job_cancel", [sys.executable, "-c", "import time; time.sleep(60)"],
        tmp_path, 30, tmp_path / "run.log"
    ))
    proc = None
    try:
        async with asyncio.timeout(5):
            while not research._PROCS:
                await asyncio.sleep(0.01)
        proc = next(iter(research._PROCS))
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        # The awaited cancellation must finish cleanup, rather than hiding an
        # orphan from shutdown by removing its only tracked process reference.
        assert proc.returncode is not None
        assert not research._PROCS
    finally:
        if not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        if proc is not None and proc.returncode is None:
            os.killpg(proc.pid, signal.SIGKILL)
            await proc.wait()


@pytest.mark.parametrize("existing", [False, True])
async def test_raw_worker_log_is_owner_private(tmp_path, recorded_states, existing):
    path = tmp_path / "logs" / "run.log"
    if existing:
        path.parent.mkdir()
        path.write_text("prior output")
        path.chmod(0o644)
    previous = os.umask(0o022)
    try:
        await research.run(None, "job_log", [sys.executable, "-c", "print('private marker')"],
                           tmp_path, 5, path)
    finally:
        os.umask(previous)
    assert path.read_text().strip() == "private marker"
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    if not existing:
        assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700


@pytest.mark.parametrize("exit_code", [0, 3])
async def test_safe_start_and_terminal_events(tmp_path, recorded_states, caplog, exit_code):
    caplog.set_level("INFO", logger=research.__name__)
    private = "synthetic-private-worker-material"
    await research.run(None, "job_audit", [sys.executable, "-c",
                       f"print({private!r}); raise SystemExit({exit_code})"],
                       tmp_path, 5, tmp_path / "run.log")
    assert "research_job_started job_id=job_audit" in caplog.text
    expected = "done" if exit_code == 0 else "failed"
    event = f"research_job_finished job_id=job_audit status={expected} exit_code={exit_code}"
    assert event in caplog.text
    assert private not in caplog.text
    assert str(tmp_path) not in caplog.text


async def test_launch_failure_log_excludes_exception_text(tmp_path, recorded_states,
                                                         caplog, monkeypatch):
    async def unavailable(*args, **kwargs):
        raise OSError("synthetic-secret-path-or-provider-body")

    monkeypatch.setattr(research.asyncio, "create_subprocess_exec", unavailable)
    caplog.set_level("INFO", logger=research.__name__)
    await research.run(None, "job_launch", ["not-used"], tmp_path, 5, tmp_path / "run.log")
    assert recorded_states[-1]["status"] == "failed"
    assert "research_job_failed job_id=job_launch error=OSError" in caplog.text
    assert "synthetic-secret" not in caplog.text
    assert str(tmp_path) not in caplog.text


async def test_task_callback_log_excludes_exception_text(caplog):
    async def fail():
        raise RuntimeError("synthetic-secret-database-parameter")

    task = asyncio.create_task(fail())
    await asyncio.gather(task, return_exceptions=True)
    research._report(task)
    assert "error=RuntimeError" in caplog.text
    assert "synthetic-secret" not in caplog.text


class ControlledProcess:
    pid = 12345
    returncode = None

    def __init__(self):
        self.waiting = asyncio.Event()
        self.reaped = asyncio.Event()

    async def wait(self):
        self.waiting.set()
        await self.reaped.wait()
        self.returncode = -signal.SIGKILL
        return self.returncode


async def test_repeated_cancel_waits_for_reaping(tmp_path, recorded_states, monkeypatch):
    proc = ControlledProcess()
    killed = asyncio.Event()

    async def spawn(*args, **kwargs):
        return proc

    monkeypatch.setattr(research.asyncio, "create_subprocess_exec", spawn)
    monkeypatch.setattr(research, "_kill", lambda current: killed.set())
    task = asyncio.create_task(research.run(None, "job_repeat", ["fake"], tmp_path, 5,
                                            tmp_path / "run.log"))
    try:
        await proc.waiting.wait()
        task.cancel()
        await asyncio.wait_for(killed.wait(), 1)
        task.cancel()
        await asyncio.sleep(0)
        assert not task.done()
        assert proc in research._PROCS
        task.cancel()
        await asyncio.sleep(0)
        assert not task.done()
    finally:
        proc.reaped.set()
        await asyncio.gather(task, return_exceptions=True)
    assert task.cancelled()
    assert not research._PROCS
    assert recorded_states[-1]["status"] == "cancelled"


async def test_cancel_during_spawn_still_reaps_child(tmp_path, recorded_states, monkeypatch):
    proc = ControlledProcess()
    spawning = asyncio.Event()
    finish_spawn = asyncio.Event()
    killed = []

    async def spawn(*args, **kwargs):
        spawning.set()
        await finish_spawn.wait()
        return proc

    def kill(current):
        killed.append(current)
        current.reaped.set()

    monkeypatch.setattr(research.asyncio, "create_subprocess_exec", spawn)
    monkeypatch.setattr(research, "_kill", kill)
    task = asyncio.create_task(research.run(None, "job_spawn", ["fake"], tmp_path, 5,
                                            tmp_path / "run.log"))
    try:
        await spawning.wait()
        task.cancel()
        await asyncio.sleep(0)
        assert not task.done()
    finally:
        finish_spawn.set()
        await asyncio.gather(task, return_exceptions=True)
    assert task.cancelled()
    assert killed == [proc]
    assert proc.returncode is not None
    assert not research._PROCS


async def test_timeout_retains_stderr_in_private_log(tmp_path, recorded_states, caplog):
    caplog.set_level("INFO", logger=research.__name__)
    path = tmp_path / "run.log"
    await research.run(None, "job_timeout", [sys.executable, "-c",
                       "import sys,time; print('private stderr',file=sys.stderr,flush=True); "
                       "time.sleep(60)"], tmp_path, 0.3, path)
    assert recorded_states[-1]["status"] == "failed"
    assert "timed out" in recorded_states[-1]["error"]
    assert path.read_text().strip() == "private stderr"
    assert "status=failed timed_out=true" in caplog.text
    assert "private stderr" not in caplog.text
    assert not research._PROCS


async def test_shutdown_kills_and_reaps_live_run(tmp_path, recorded_states):
    task = asyncio.create_task(research.run(
        None, "job_shutdown", [sys.executable, "-c", "import time; time.sleep(60)"],
        tmp_path, 5, tmp_path / "run.log"
    ))
    proc = None
    try:
        async with asyncio.timeout(5):
            while not research._PROCS:
                await asyncio.sleep(0.01)
        proc = next(iter(research._PROCS))
        research.shutdown()
        await asyncio.wait_for(task, 2)
        assert proc.returncode == -signal.SIGKILL
        assert recorded_states[-1]["status"] == "failed"
        assert not research._PROCS
    finally:
        if not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        if proc is not None and proc.returncode is None:
            os.killpg(proc.pid, signal.SIGKILL)
            await proc.wait()


async def test_log_wrapper_failure_closes_owned_fd(tmp_path, recorded_states, monkeypatch):
    opened = []

    def unavailable(fd, *args, **kwargs):
        opened.append(fd)
        raise OSError("synthetic wrapper failure")

    monkeypatch.setattr(research.os, "fdopen", unavailable)
    await research.run(None, "job_fd", ["not-started"], tmp_path, 5, tmp_path / "run.log")
    assert recorded_states[-1]["status"] == "failed"
    assert len(opened) == 1
    with pytest.raises(OSError):
        os.fstat(opened[0])


async def test_unavailable_database_cannot_hold_cancelled_waiter(tmp_path, recorded_states,
                                                               caplog, monkeypatch):
    proc = ControlledProcess()

    async def spawn(*args, **kwargs):
        return proc

    async def unavailable(*args, **kwargs):
        if kwargs.get("status") == "cancelled":
            await asyncio.Event().wait()

    monkeypatch.setattr(research.asyncio, "create_subprocess_exec", spawn)
    monkeypatch.setattr(research, "_set", unavailable)
    monkeypatch.setattr(research, "_kill", lambda current: current.reaped.set())
    monkeypatch.setattr(research, "PROCESS_CLEANUP_TIMEOUT_SECONDS", 0.05)
    task = asyncio.create_task(research.run(None, "job_db", ["fake"], tmp_path, 5,
                                            tmp_path / "run.log"))
    await proc.waiting.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await asyncio.wait_for(task, 1)
    assert proc.returncode is not None
    assert not research._PROCS
    assert "research_job_cleanup_failed job_id=job_db error=TimeoutError" in caplog.text
