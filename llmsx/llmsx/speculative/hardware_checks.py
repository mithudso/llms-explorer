"""Native abort/retry and boundary probes. These require a running loaded target."""
from __future__ import annotations

import uuid
from dataclasses import asdict

from .protocol import ProtocolError, expected_state


def check_native_cache(target, prompt):
    prefix = target.encode(prompt, add_bos=None)
    info = target.describe()
    identifier = uuid.uuid4().hex
    opened = []
    failed = False
    try:
        opened.append(identifier)
        original = target.open(prefix, session_id=identifier)
        if original != expected_state(identifier, 0, prefix):
            raise ProtocolError("Cache probe open acknowledgement differs from prefix")
        first = target.verify(original, ()).target_ids[0]
        reply = target.rpc("rollback", state=asdict(original))
        if target._state(reply) != original:
            raise ProtocolError("Rollback changed the committed state")
        wrong = (first + 1) % info.vocab_size
        branch = target.verify(original, (wrong,) * 4)
        if branch.target_ids[0] != first:
            raise ProtocolError("First prediction changed after rollback")
        rejected = False
        try:
            target.commit(original, (wrong,))
        except ProtocolError:
            rejected = True
        if not rejected:
            raise ProtocolError("Native target accepted an unverified correction")
        target.rpc("rollback", state=asdict(original))
        restored = target.rpc("state", session_id=identifier)
        if (target._state(restored) != original or restored["pending_verification"]
                or any(offset not in (-1, len(prefix)-1) for offset in restored["cache_offsets"])):
            raise ProtocolError("Rollback did not restore all committed cache offsets")
        retried = target.verify(original, ()).target_ids[0]
        if retried != first:
            raise ProtocolError("Aborted branch changed the next target token")
        committed = target.commit(original, (retried,))
        if committed != expected_state(identifier, 1, prefix + (retried,)):
            raise ProtocolError("Commit acknowledgement differs from authoritative history")
        next_token = target.verify(committed, ()).target_ids[0]
        fresh_id = identifier + "-fresh"
        # One native session by default: retain IDs then discard the first cache.
        target.close(identifier)
        opened.remove(identifier)
        opened.append(fresh_id)
        fresh = target.open(prefix + (retried,), session_id=fresh_id)
        if fresh != expected_state(fresh_id, 0, prefix + (retried,)):
            raise ProtocolError("Fresh cache open acknowledgement differs from prefix")
        fresh_next = target.verify(fresh, ()).target_ids[0]
        if fresh_next != next_token:
            raise ProtocolError("Rollback continuation differs from a fresh cache")
        unicode_checks = []
        for text in ("é", "🙂", "\U0010ffff"):
            ids = target.encode(text)
            for length in range(1, len(ids)+1):
                decoded = target.rpc("decode", token_ids=list(ids[:length]))
                unicode_checks.append({"source": text, "prefix_ids": list(ids[:length]),
                                       "valid_utf8": decoded.get("valid_utf8")})
        return {"status": "cache_checks_pass", "prefix_token_count": len(prefix),
                "rollback_state": restored, "first_token": first, "next_token": next_token,
                "fresh_next_token": fresh_next, "invalid_commit_rejected": rejected,
                "unicode_checks": unicode_checks, "target": target.metadata}
    except BaseException:
        failed = True
        raise
    finally:
        close_errors = []
        for owned_id in reversed(opened):
            try:
                target.close(owned_id)
            except Exception as exc:
                close_errors.append(exc)
        if close_errors and not failed:
            raise ProtocolError("A cache-probe session could not be closed") from close_errors[0]
