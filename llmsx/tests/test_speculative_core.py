"""Token/cache/transport contracts, using an independent autoregressive oracle.

These tests prove the coordinator contract with CPU test doubles. They do not
qualify a model, a real MLX cache or a GPU backend's block-forward semantics.
"""
from dataclasses import replace

import pytest

from llmsx.speculative import (
    BackendDescription,
    CancelledError,
    GreedyCoordinator,
    Proposal,
    ProtocolError,
    SessionState,
    StreamMetrics,
    Verification,
    expected_state,
    prefix_digest,
    tokenizer_fingerprint,
)

VOCAB = 257
FINGERPRINT = tokenizer_fingerprint({
    "vocabulary": [str(i) for i in range(VOCAB)],
    "normalizer": "none", "special_tokens": {"bos": 1},
})


def oracle_next(prefix):
    # History-dependent, independent of the coordinator or acceptance algorithm.
    return (sum((i + 3) * (token + 7) for i, token in enumerate(prefix))
            + 11 * len(prefix)) % VOCAB


def oracle_generate(prefix, count, eos=()):
    history = list(prefix)
    output = []
    for _ in range(count):
        token = oracle_next(history)
        history.append(token)
        output.append(token)
        if token in eos:
            break
    return tuple(output)


class CacheBackend:
    """Simulate a rotating cache overwritten by speculative branches."""

    def __init__(self, *, target=False, reject_at=None, window=4, empty=False):
        self.target = target
        self.reject_at = reject_at
        self.window = window
        self.empty = empty
        self.sessions = {}
        self.closed = []
        self.commits = []
        self.verify_calls = []
        self.snapshots = []
        self.info = BackendDescription(
            "target" if target else "draft", "oracle-target" if target else "oracle-draft",
            FINGERPRINT, VOCAB, 1000, not target, target, True, (1,))

    def describe(self):
        return self.info

    def open(self, prefix_ids, *, session_id):
        self.sessions[session_id] = {
            "prefix": list(prefix_ids), "ring": list(prefix_ids[-self.window:]),
            "position": len(prefix_ids), "round": 0, "checkpoint": None,
        }
        return expected_state(session_id, 0, prefix_ids)

    def _session(self, state):
        session = self.sessions[state.session_id]
        assert state == expected_state(state.session_id, session["round"], session["prefix"])
        return session

    def _checkpoint(self, session):
        assert session["checkpoint"] is None
        session["checkpoint"] = (list(session["ring"]), session["position"])
        self.snapshots.append(tuple(session["ring"]))

    def _append_cache(self, session, token):
        session["ring"].append(token)
        session["ring"][:] = session["ring"][-self.window:]
        session["position"] += 1

    def propose(self, state, count):
        session = self._session(state)
        self._checkpoint(session)
        branch = list(session["prefix"])
        output = []
        for index in range(0 if self.empty else count):
            token = oracle_next(branch)
            if self.reject_at is not None and index == self.reject_at:
                token = (token + 1) % VOCAB
            output.append(token)
            branch.append(token)
            self._append_cache(session, token)
        return Proposal(state, tuple(output))

    def verify(self, state, token_ids):
        session = self._session(state)
        self._checkpoint(session)
        branch = list(session["prefix"])
        # This stands for one block forward, not repeated HTTP completions.
        self.verify_calls.append(token_ids)
        predictions = []
        for token in token_ids:
            predictions.append(oracle_next(branch))
            branch.append(token)
            self._append_cache(session, token)
        predictions.append(oracle_next(branch))
        return Verification(state, tuple(predictions))

    def commit(self, state, token_ids):
        session = self._session(state)
        saved_ring, saved_position = session["checkpoint"]
        session["ring"] = list(saved_ring)
        session["position"] = saved_position
        session["checkpoint"] = None
        for token in token_ids:
            self._append_cache(session, token)
        session["prefix"].extend(token_ids)
        session["round"] += 1
        # Assert cache contents and absolute position, not only prefix text.
        assert session["ring"] == session["prefix"][-self.window:]
        assert session["position"] == len(session["prefix"])
        self.commits.append(tuple(session["prefix"]))
        return expected_state(state.session_id, session["round"], session["prefix"])

    def close(self, session_id):
        self.closed.append(session_id)
        self.sessions.pop(session_id, None)


def collect(draft, target, prefix=(2, 5, 7), **kwargs):
    blocks = list(GreedyCoordinator(draft, target).generate(
        prefix, max_new_tokens=kwargs.pop("max_new_tokens", 17), **kwargs))
    return tuple(token for block in blocks for token in block.token_ids), blocks


@pytest.mark.parametrize("reject_at", [0, 1, 3, None])
@pytest.mark.parametrize("prefix", [(2,), (2, 5, 7), (2, 5, 7, 11, 13, 17)])
def test_greedy_parity_and_rollback_across_rotating_window(reject_at, prefix):
    draft = CacheBackend(reject_at=reject_at)
    target = CacheBackend(target=True)
    output, blocks = collect(draft, target, prefix)
    assert output == oracle_generate(prefix, 17)
    assert draft.commits == target.commits
    assert blocks[-1].finish_reason == "max_tokens"
    assert all(len(proposals) <= 4 for proposals in target.verify_calls)
    assert len(target.verify_calls) == len(blocks)
    assert draft.closed and target.closed
    assert not draft.sessions and not target.sessions
    assert any(len(snapshot) == draft.window for snapshot in draft.snapshots)
    assert all(block.metrics.accepted_draft_tokens <= block.metrics.committed_tokens
               for block in blocks)


@pytest.mark.parametrize("length", [1, 2, 4, 8])
@pytest.mark.parametrize("limit", [1, 2, 3, 5])
def test_output_cap_and_bonus_never_exceed_limit(length, limit):
    output, blocks = collect(CacheBackend(), CacheBackend(target=True),
                             draft_length=length, max_new_tokens=limit)
    assert output == oracle_generate((2, 5, 7), limit)
    assert sum(b.metrics.committed_tokens for b in blocks) == limit
    assert blocks[-1].finish_reason == "max_tokens"


@pytest.mark.parametrize("eos_index", [0, 1, 3, 4, 6])
def test_eos_in_accepted_prefix_correction_or_bonus(eos_index):
    prefix = (2, 5, 7)
    wanted = oracle_generate(prefix, 10)
    eos = (wanted[eos_index],)
    for reject_at in (0, 1, 3, None):
        output, blocks = collect(CacheBackend(reject_at=reject_at),
                                 CacheBackend(target=True), eos_token_ids=eos)
        assert output == oracle_generate(prefix, 17, eos)
        assert blocks[-1].finish_reason == "eos"
        assert output[-1] in eos


def test_empty_draft_is_explicit_target_only_progress():
    output, blocks = collect(CacheBackend(empty=True), CacheBackend(target=True))
    assert output == oracle_generate((2, 5, 7), 17)
    assert all(b.metrics.proposed_tokens == 0 and b.metrics.accepted_draft_tokens == 0
               for b in blocks)
    assert all(len(b.token_ids) == 1 for b in blocks)


def test_only_emit_after_both_commits_and_close_on_iterator_discard():
    draft, target = CacheBackend(), CacheBackend(target=True)
    iterator = GreedyCoordinator(draft, target).generate((2, 5), max_new_tokens=12)
    block = next(iterator)
    assert draft.commits == target.commits == [(2, 5) + block.token_ids]
    iterator.close()
    assert draft.closed and target.closed


@pytest.mark.parametrize("change", [
    {"tokenizer_fingerprint": tokenizer_fingerprint({"vocabulary": ["B", "A"]})},
    {"tokenizer_fingerprint": tokenizer_fingerprint({"normalizer": "NFKC"})},
    {"special_token_ids": (2,)}, {"vocab_size": VOCAB + 1},
    {"protocol_version": 2}, {"supports_rollback": False},
])
def test_incompatible_metadata_fails_before_open(change):
    draft, target = CacheBackend(), CacheBackend(target=True)
    draft.info = replace(draft.info, **change)
    with pytest.raises(ProtocolError):
        collect(draft, target)
    assert not draft.sessions and not target.sessions
    assert not draft.closed and not target.closed


@pytest.mark.parametrize("change", [
    {"supports_verify": False}, {"verification_mode": "sampled-text"},
])
def test_target_requires_real_block_verifier(change):
    draft, target = CacheBackend(), CacheBackend(target=True)
    target.info = replace(target.info, **change)
    with pytest.raises(ProtocolError):
        collect(draft, target)
    assert not target.sessions


@pytest.mark.parametrize("method", ["open", "propose", "verify", "commit"])
def test_backend_exception_closes_both_attempted_owned_sessions(method):
    draft, target = CacheBackend(), CacheBackend(target=True)
    backend = draft if method == "propose" else target
    setattr(backend, method, lambda *args, **kwargs: (_ for _ in ()).throw(
        OSError("injected backend failure")))
    with pytest.raises(OSError, match="injected"):
        collect(draft, target)
    assert draft.closed and target.closed
    assert not draft.sessions and not target.sessions


@pytest.mark.parametrize("failure", ["proposal_state", "proposal_size", "proposal_token",
                                     "verify_state", "verify_size", "verify_token", "commit"])
def test_invalid_backend_results_are_fail_closed(failure):
    draft, target = CacheBackend(), CacheBackend(target=True)
    if failure.startswith("proposal"):
        original = draft.propose

        def propose(state, count):
            result = original(state, count)
            if failure == "proposal_state":
                return Proposal(replace(state, round_id=99), result.token_ids)
            return Proposal(state, (999,) if failure == "proposal_token"
                            else result.token_ids + (0,))

        draft.propose = propose
    elif failure.startswith("verify"):
        original = target.verify

        def verify(state, tokens):
            result = original(state, tokens)
            if failure == "verify_state":
                return Verification(replace(state, prefix_digest="wrong"), result.target_ids)
            return Verification(state, (999,) * len(result.target_ids)
                                if failure == "verify_token" else result.target_ids[:-1])

        target.verify = verify
    else:
        original = draft.commit
        draft.commit = lambda state, tokens: replace(original(state, tokens), position=999)
    with pytest.raises(ProtocolError):
        collect(draft, target)
    assert draft.closed and target.closed
    assert not draft.sessions and not target.sessions


@pytest.mark.parametrize("cancel_after", ["open", "propose", "verify", "commit"])
def test_cancellation_emits_no_unacknowledged_tokens(cancel_after):
    draft, target = CacheBackend(), CacheBackend(target=True)
    cancelled = False
    backend = draft if cancel_after == "propose" else target
    original = getattr(backend, cancel_after)

    def operation(*args, **kwargs):
        nonlocal cancelled
        result = original(*args, **kwargs)
        cancelled = True
        return result

    setattr(backend, cancel_after, operation)
    output = []
    with pytest.raises(CancelledError):
        for block in GreedyCoordinator(draft, target).generate(
                (2, 5), max_new_tokens=7, cancel=lambda: cancelled):
            output.extend(block.token_ids)
    assert output == []
    assert draft.closed and target.closed
    assert not draft.sessions and not target.sessions


def test_preexisting_cancellation_opens_no_sessions():
    draft, target = CacheBackend(), CacheBackend(target=True)
    with pytest.raises(CancelledError):
        collect(draft, target, cancel=lambda: True)
    assert not draft.closed and not target.closed


def test_cleanup_does_not_mask_original_failure_and_attempts_other_close():
    draft, target = CacheBackend(), CacheBackend(target=True)
    target.verify = lambda *args: (_ for _ in ()).throw(OSError("original failure"))
    target.close = lambda *args: (_ for _ in ()).throw(OSError("close failure"))
    with pytest.raises(OSError, match="original failure"):
        collect(draft, target)
    assert draft.closed


def test_close_failure_after_success_is_reported():
    draft, target = CacheBackend(), CacheBackend(target=True)
    target.close = lambda *args: (_ for _ in ()).throw(OSError("close failure"))
    with pytest.raises(ProtocolError, match="could not be closed"):
        collect(draft, target)
    assert draft.closed


def test_zero_output_and_capacity_are_checked_without_open():
    draft, target = CacheBackend(), CacheBackend(target=True)
    assert collect(draft, target, max_new_tokens=0) == ((), [])
    assert not draft.closed and not target.closed
    draft.info = replace(draft.info, max_context=3)
    with pytest.raises(ValueError, match="fit both contexts"):
        collect(draft, target, max_new_tokens=1)
    assert not draft.closed


@pytest.mark.parametrize("tokens", [(True,), (-1,), (2**32,), (1.2,)])
def test_prefix_digest_rejects_ambiguous_or_invalid_ids(tokens):
    with pytest.raises(ValueError):
        prefix_digest(tokens)


def test_fingerprints_retain_order_and_normalization_and_ids():
    one = {"vocabulary": ["A", "B"], "normalizer": "none", "special": {"bos": 0}}
    assert tokenizer_fingerprint(one) == tokenizer_fingerprint(dict(reversed(list(one.items()))))
    for change in ({"vocabulary": ["B", "A"]}, {"normalizer": "NFKC"},
                   {"special": {"bos": 1}}):
        assert tokenizer_fingerprint(one) != tokenizer_fingerprint({**one, **change})
    assert prefix_digest((1, 23)) != prefix_digest((12, 3))


def test_metrics_observe_actual_committed_ids_and_keep_unknown_gpu_time_null():
    metrics = StreamMetrics(1_000_000_000)
    metrics.observe(3, 2_000_000_000)
    metrics.mark_visible(2_100_000_000)
    metrics.observe(1, 3_000_000_000, visible=True)
    metrics.finish(5_000_000_000)
    summary = metrics.summary()
    assert summary["committed_tokens"] == 4
    assert summary["ttft_seconds"] == 1.0
    assert summary["first_visible_seconds"] == 1.1
    assert summary["committed_tokens_per_wall_second"] == 1.0
    assert summary["inter_token_seconds"] == [0.0, 0.0, 1.0]
    assert summary["backend_gpu_seconds"] is None
    assert summary["acceptance_fraction"] is None
    with pytest.raises(ValueError):
        metrics.observe(1, 6_000_000_000)


def test_unknown_metrics_remain_unknown():
    summary = StreamMetrics(0).summary()
    assert summary["ttft_seconds"] is None
    assert summary["wall_seconds"] is None
    assert summary["committed_tokens_per_wall_second"] is None


def test_session_state_is_frozen():
    state = SessionState("s", 0, prefix_digest((1,)), 1)
    with pytest.raises(AttributeError):
        state.round_id = 2
