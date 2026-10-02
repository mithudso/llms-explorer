"""Independent greedy draft/target token protocol; hardware support is adapter-specific."""
from .core import CommittedBlock, GreedyCoordinator
from .metrics import RoundMetrics, StreamMetrics
from .protocol import (
    PROTOCOL_VERSION,
    Backend,
    BackendDescription,
    CancelledError,
    Proposal,
    ProtocolError,
    SessionState,
    Verification,
    expected_state,
    prefix_digest,
    tokenizer_fingerprint,
)

__all__ = [
    "PROTOCOL_VERSION", "Backend", "BackendDescription", "CancelledError",
    "CommittedBlock", "GreedyCoordinator", "Proposal", "ProtocolError", "RoundMetrics",
    "SessionState", "StreamMetrics", "Verification", "expected_state", "prefix_digest",
    "tokenizer_fingerprint",
]
