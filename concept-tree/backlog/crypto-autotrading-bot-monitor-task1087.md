# Crypto autotrading bot monitor — manual dissent backlog

This is a documentation-only backlog for TASK-1087. It contains three unresearched procedure/evidence gaps after the default three rounds. Fifteen source concepts and 320 assertions remain accepted. The current small/full reader contract qualifies 13 of 15 packs; market data scores 7/10 and 8/10, and evidence/latency contracts score 6/10 and 8/10.

## Registration limit

The installed queue steward and frontier runner have no durable per-item hold. A `Queue-state: held` annotation would not enforce a hold. No unchecked queue jobs, frontier child edges, CVS sidecar entries or reservations are added for these items. These records live outside the inspected consumers’ recognized inputs. This is not machine-ready registration or a scheduler-enforced hold.

A separately authorized run must explicitly promote a selected item after checking its budget, source/gate contract and pause ownership. Do not automatically start a fourth round. Preserve every existing queue entry, reservation and pause.

## Unresearched gaps

### TASK1087-DISSENT-01 — Crypto bot stream reconnect resubscribe and rebootstrap procedure

Parent: Crypto bot market-data freshness and stream integrity. CVS: 4.45; threshold: 3.2. Status: manual-only, unresearched.

Accepted source facts cover missing-update resynchronization and recovery prerequisites, but not a concrete disconnected-stream reconnection, subscription restoration and usable-state rebootstrap procedure.

Evidence:
- crypto-bot-market-data-freshness-and-stream-integrity:full:Q5; report TASK1087.market-independent-grading.v3; report SHA-256 012735faafcfbf60e395a90936a16b49e1b6c1ac8c9ff57bb3a8c36b7d6ac59d; frozen bank SHA-256 9969b222dba6ac89f0913211f6db76beab8be424263efebafa6d308b279b43dd.

### TASK1087-DISSENT-02 — Crypto bot duplicate event evidence retention and presentation

Parent: Crypto bot monitor evidence and latency contracts. CVS: 4.45; threshold: 3.2. Status: manual-only, unresearched.

Independent marketQ7 and evidence-contractQ8 both corroborate missing duplicate-observation retention/presentation behavior; choosing keys or injecting duplicates does not define evidence treatment.

Evidence:
- crypto-bot-market-data-freshness-and-stream-integrity:full:Q7; report TASK1087.market-independent-grading.v3; report SHA-256 012735faafcfbf60e395a90936a16b49e1b6c1ac8c9ff57bb3a8c36b7d6ac59d; frozen bank SHA-256 9969b222dba6ac89f0913211f6db76beab8be424263efebafa6d308b279b43dd.
- crypto-bot-monitor-evidence-and-latency-contracts:full:Q8; report TASK1087.evidence-independent-grading.v3; report SHA-256 c2c1f658243229636c4dc9e14ed9159e979a7f874cea326e360dc4bf99a7820f; frozen bank SHA-256 0fbb369b2645489a0814ba6248694173d4c39b7cf76419c0da2fbf052aa14eb1.

### TASK1087-DISSENT-03 — Crypto bot incident grouping deduplication update and reopening procedure

Parent: Crypto bot monitor evidence and latency contracts. CVS: 4.45; threshold: 3.2. Status: manual-only, unresearched.

The actual evidence-contract FULL Q2 answer supplies escalation/policy/ACK caveats but leaves incident grouping, deduplication, updating and reopening as choices rather than operational decision rules.

Evidence:
- crypto-bot-monitor-evidence-and-latency-contracts:full:Q2; report TASK1087.evidence-independent-grading.v3; report SHA-256 c2c1f658243229636c4dc9e14ed9159e979a7f874cea326e360dc4bf99a7820f; frozen bank SHA-256 0fbb369b2645489a0814ba6248694173d4c39b7cf76419c0da2fbf052aa14eb1.

## Evidence and source boundaries

The shared duplicate-event gap is counted once across the market-data and evidence-contract questions. Incident grouping/lifecycle rules are a separate gap from retained observation evidence and presentation. These are missing procedures, not demands for a completed deployment, universal algorithm or numeric default.

Existing factual claims and conditional PROPOSED summaries remain exact. Future procedure/design choices must retain their qualification and receive the required native review. No new source facts, executed tests, recovery success or native research failure is asserted here. Bounded SATURATION-DISSENT is not coverage success or a passing grade for the two rejected packs.
