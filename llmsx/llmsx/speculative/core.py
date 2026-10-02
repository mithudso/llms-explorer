"""Fail-closed greedy speculation over independent persistent token backends."""
from __future__ import annotations

import time
import uuid
from collections.abc import Callable, Iterator
from dataclasses import dataclass

from .metrics import RoundMetrics
from .protocol import (
    PROTOCOL_VERSION,
    Backend,
    CancelledError,
    ProtocolError,
    SessionState,
    expected_state,
    validate_tokens,
)


@dataclass(frozen=True)
class CommittedBlock:
    token_ids: tuple[int, ...]
    round_id: int
    state: SessionState
    metrics: RoundMetrics
    arrived_ns: int
    finish_reason: str | None = None


class GreedyCoordinator:
    def __init__(self, draft: Backend, target: Backend,
                 *, clock_ns: Callable[[], int] = time.perf_counter_ns) -> None:
        self.draft = draft
        self.target = target
        self.clock_ns = clock_ns

    def generate(self, prefix_ids: tuple[int, ...], *, max_new_tokens: int,
                 draft_length: int = 4, eos_token_ids: tuple[int, ...] = (),
                 cancel: Callable[[], bool] | None = None,
                 session_id: str | None = None) -> Iterator[CommittedBlock]:
        """Yield only after both backends acknowledge the committed prefix.

        The target remains authoritative. This implements greedy acceptance only;
        it cannot preserve a stochastic distribution by comparing sampled tokens.
        Any error or cancellation closes both owned sessions, including a partial
        commit. No backend caches survive for an uncertain retry.
        """
        for value, minimum in ((max_new_tokens, 0), (draft_length, 1)):
            if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
                raise ValueError("Output limit and draft length must be valid integers")
        if not isinstance(prefix_ids, tuple) or not isinstance(eos_token_ids, tuple):
            raise ValueError("Prefix and EOS IDs must be immutable tuples")
        draft_info, target_info = self.draft.describe(), self.target.describe()
        for description in (draft_info, target_info):
            if description.protocol_version != PROTOCOL_VERSION:
                raise ProtocolError("Unsupported speculative protocol version")
            if not description.supports_rollback:
                raise ProtocolError("Both backends must restore round checkpoints")
        if not draft_info.supports_propose or not target_info.supports_verify:
            raise ProtocolError("Draft proposing and target block verification are required")
        if target_info.verification_mode != "greedy-block":
            raise ProtocolError("Target must provide greedy causal block verification")
        if (draft_info.tokenizer_fingerprint != target_info.tokenizer_fingerprint
                or draft_info.vocab_size != target_info.vocab_size
                or draft_info.special_token_ids != target_info.special_token_ids):
            raise ProtocolError("Draft and target tokenizers are incompatible")
        validate_tokens(prefix_ids, target_info.vocab_size)
        validate_tokens(eos_token_ids, target_info.vocab_size)
        capacity = min(draft_info.max_context, target_info.max_context)
        if not prefix_ids or len(prefix_ids) + max_new_tokens > capacity:
            raise ValueError("Nonempty prefix and requested output must fit both contexts")
        if max_new_tokens == 0:
            return

        def check_cancelled() -> None:
            if cancel is not None and cancel():
                raise CancelledError("Speculative generation cancelled")

        def acknowledge(actual: SessionState, expected: SessionState) -> SessionState:
            if actual != expected:
                raise ProtocolError("Backend acknowledged a stale or inconsistent prefix")
            return actual

        committed = prefix_ids
        generated = 0
        identifier = session_id or uuid.uuid4().hex
        opened: list[tuple[Backend, str]] = []
        failed = False
        try:
            check_cancelled()
            # Separate session IDs also permit two models hosted by one server.
            draft_id, target_id = identifier + "-draft", identifier + "-target"
            opened.append((self.draft, draft_id))
            draft_state = acknowledge(
                self.draft.open(committed, session_id=draft_id),
                expected_state(draft_id, 0, committed))
            check_cancelled()
            opened.append((self.target, target_id))
            target_state = acknowledge(
                self.target.open(committed, session_id=target_id),
                expected_state(target_id, 0, committed))
            check_cancelled()
            while generated < max_new_tokens:
                remaining = max_new_tokens - generated
                count = min(draft_length, remaining)
                start = self.clock_ns()
                proposal = self.draft.propose(draft_state, count)
                draft_ns = self.clock_ns() - start
                check_cancelled()
                if proposal.state != draft_state:
                    raise ProtocolError("Draft proposal has a stale session or prefix")
                if (not isinstance(proposal.token_ids, tuple)
                        or not 0 <= len(proposal.token_ids) <= count):
                    raise ProtocolError("Draft returned an oversized proposal")
                try:
                    validate_tokens(proposal.token_ids, target_info.vocab_size)
                except ValueError as exc:
                    raise ProtocolError(str(exc)) from exc
                start = self.clock_ns()
                verification = self.target.verify(target_state, proposal.token_ids)
                verify_ns = self.clock_ns() - start
                check_cancelled()
                if verification.state != target_state:
                    raise ProtocolError("Target verification has a stale session or prefix")
                if (not isinstance(verification.target_ids, tuple)
                        or len(verification.target_ids) != len(proposal.token_ids) + 1):
                    raise ProtocolError("Target must score each proposal plus its bonus token")
                try:
                    validate_tokens(verification.target_ids, target_info.vocab_size)
                except ValueError as exc:
                    raise ProtocolError(str(exc)) from exc
                accepted = 0
                for draft_token, target_token in zip(
                        proposal.token_ids, verification.target_ids, strict=False):
                    if draft_token != target_token:
                        break
                    accepted += 1
                block = (proposal.token_ids[:accepted]
                         + (verification.target_ids[accepted],))[:remaining]
                finish_reason = None
                for index, token in enumerate(block):
                    if token in eos_token_ids:
                        block = block[:index + 1]
                        finish_reason = "eos"
                        break
                generated += len(block)
                if generated == max_new_tokens and finish_reason is None:
                    finish_reason = "max_tokens"
                next_prefix = committed + block
                next_round = target_state.round_id + 1
                start = self.clock_ns()
                target_state = acknowledge(
                    self.target.commit(target_state, block),
                    expected_state(target_id, next_round, next_prefix))
                check_cancelled()
                draft_state = acknowledge(
                    self.draft.commit(draft_state, block),
                    expected_state(draft_id, next_round, next_prefix))
                check_cancelled()
                commit_ns = self.clock_ns() - start
                committed = next_prefix
                metrics = RoundMetrics(len(proposal.token_ids), min(accepted, len(block)),
                                       len(block), draft_ns, verify_ns, commit_ns)
                yield CommittedBlock(block, next_round, target_state, metrics,
                                     self.clock_ns(), finish_reason)
                if finish_reason:
                    return
                check_cancelled()
        except BaseException:
            failed = True
            raise
        finally:
            close_errors = []
            for backend, owned_id in reversed(opened):
                try:
                    backend.close(owned_id)
                except Exception as exc:
                    close_errors.append(exc)
            if close_errors and not failed:
                error = ProtocolError("An owned backend session could not be closed")
                raise error from close_errors[0]
