"""runner.py — run hub scripts as subprocesses with line-streamed output.

ProcJob spawns argv, a reader thread appends stdout+stderr lines to a bounded
deque, and an optional callback fires per line (the TUI feeds RichLog with
it). terminate() kills the whole process group so stage children die too.
"""

from __future__ import annotations

import collections
import os
import queue
import signal
import subprocess
import threading
import time
from pathlib import Path


class ProcJob:
    def __init__(self, argv: list[str], env: dict | None = None,
                 cwd: Path | None = None, on_line=None, max_lines: int = 5000):
        self.argv = argv
        self.on_line = on_line
        self.lines: collections.deque[str] = collections.deque(maxlen=max_lines)
        # Lines pending UI display; drained in batches by a timer so a chatty
        # child can't flood the event loop with one callback per line.
        self.ui_queue: queue.SimpleQueue[str] = queue.SimpleQueue()
        self.started = time.time()
        self.returncode: int | None = None
        merged = os.environ.copy()
        if env:
            merged.update(env)
        self.proc = subprocess.Popen(
            argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1, env=merged, cwd=cwd,
            start_new_session=True)
        self._thread = threading.Thread(target=self._pump, daemon=True)
        self._thread.start()

    def _pump(self) -> None:
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            line = line.rstrip("\n")
            self._emit(line)
        self.returncode = self.proc.wait()
        self._emit(f"— exited {self.returncode} after "
                   f"{time.time() - self.started:.0f}s —")

    def _emit(self, line: str) -> None:
        self.lines.append(line)
        self.ui_queue.put(line)
        if self.on_line:
            try:
                self.on_line(line)
            except Exception:  # noqa: BLE001 — UI callback must not kill the pump
                pass

    def drain_ui(self, cap: int = 500) -> list[str]:
        """Pending display lines since the last drain (bounded per call)."""
        out: list[str] = []
        while len(out) < cap:
            try:
                out.append(self.ui_queue.get_nowait())
            except queue.Empty:
                break
        return out

    @property
    def running(self) -> bool:
        return self.proc.poll() is None

    def terminate(self) -> None:
        if not self.running:
            return
        try:
            os.killpg(os.getpgid(self.proc.pid), signal.SIGTERM)
        except OSError:
            self.proc.terminate()

    def wait(self, timeout: float | None = None) -> int | None:
        try:
            return self.proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            return None

    def text(self) -> str:
        return "\n".join(self.lines)
