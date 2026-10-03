"""Client-observed timing; these fields do not claim GPU kernel timings."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RoundMetrics:
    proposed_tokens: int
    accepted_draft_tokens: int
    committed_tokens: int
    draft_call_ns: int
    verify_call_ns: int
    commit_calls_ns: int


@dataclass
class StreamMetrics:
    """Arrival timings count committed token IDs, never whitespace words.

    Record first visible text separately from first generated tokens. Tool syntax,
    reasoning or tokenizer buffering can make those timestamps differ. A missing
    observation remains None. Call durations include serialization and transport;
    backend-synchronized load/prefill/GPU timing needs separate instrumentation.
    """

    started_ns: int
    first_generated_ns: int | None = None
    first_visible_ns: int | None = None
    finished_ns: int | None = None
    token_arrival_ns: list[int] = field(default_factory=list)
    rounds: list[RoundMetrics] = field(default_factory=list)

    def observe(self, token_count: int, arrived_ns: int, *, visible: bool = False) -> None:
        if isinstance(token_count, bool) or not isinstance(token_count, int) or token_count < 1:
            raise ValueError("An arrival must contain a positive token ID count")
        previous = self.token_arrival_ns[-1] if self.token_arrival_ns else self.started_ns
        if arrived_ns < previous or self.finished_ns is not None:
            raise ValueError("Arrival timestamps must be ordered and precede finish")
        if self.first_generated_ns is None:
            self.first_generated_ns = arrived_ns
        if visible and self.first_visible_ns is None:
            self.first_visible_ns = arrived_ns
        self.token_arrival_ns.extend([arrived_ns] * token_count)

    def mark_visible(self, arrived_ns: int) -> None:
        if self.first_generated_ns is None or arrived_ns < self.first_generated_ns:
            raise ValueError("Visible output cannot precede a generated observation")
        if self.first_visible_ns is None:
            self.first_visible_ns = arrived_ns

    def finish(self, finished_ns: int) -> None:
        previous = self.token_arrival_ns[-1] if self.token_arrival_ns else self.started_ns
        if finished_ns < previous:
            raise ValueError("Finish timestamp cannot precede token arrivals")
        self.finished_ns = finished_ns

    def summary(self) -> dict[str, object]:
        def elapsed(timestamp: int | None) -> float | None:
            return None if timestamp is None else (timestamp - self.started_ns) / 1e9

        wall = elapsed(self.finished_ns)
        intervals = [(b - a) / 1e9 for a, b in
                     zip(self.token_arrival_ns, self.token_arrival_ns[1:], strict=False)]
        proposed = sum(r.proposed_tokens for r in self.rounds)
        accepted = sum(r.accepted_draft_tokens for r in self.rounds)
        return {
            "timing_source": "client_monotonic_arrivals",
            "committed_tokens": len(self.token_arrival_ns),
            "wall_seconds": wall,
            "ttft_seconds": elapsed(self.first_generated_ns),
            "first_visible_seconds": elapsed(self.first_visible_ns),
            "committed_tokens_per_wall_second": (
                len(self.token_arrival_ns) / wall if wall and wall > 0 else None),
            "inter_token_seconds": intervals,
            "acceptance_fraction": accepted / proposed if proposed else None,
            "backend_gpu_seconds": None,
        }
