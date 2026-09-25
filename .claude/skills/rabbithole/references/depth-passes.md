# The six deepening questions

Ask all six of every claim still standing at the start of a pass. A pass that only answers
one or two questions across the whole claim list is thin; a genuine deepening pass touches
most claims with at least one question and follows the answer to a new atomic fact.

| # | Question | What it surfaces |
|---|---|---|
| 1 | Why is this true? | The mechanism underneath a stated fact |
| 2 | What happens at the boundary or limit? | Edge cases, failure modes, where the claim stops holding |
| 3 | What's the exception? | Cases the general claim doesn't cover |
| 4 | Who disagrees, and on what basis? | Expert disagreement, competing models |
| 5 | What did the primary source actually say, in its own words? | Drift between original and paraphrase |
| 6 | What changed over time in how this was understood? | Historical evolution, superseded models |

## Worked example — genuine deepening

Claim: "TCP uses slow start to grow its congestion window."

- Q1 (why): grow gradually rather than jump to the receiver's advertised window, because an
  abrupt burst would overflow a bottleneck link's queue before any feedback arrives.
- Q2 (boundary): growth is exponential only until the **slow-start threshold** (`ssthresh`);
  past it, growth switches to linear (congestion avoidance) — a genuinely new mechanism, not
  a rephrasing of the original claim.
- Q3 (exception): a loss detected via triple-duplicate-ACK (fast retransmit) does not reset
  to slow start the way a timeout does — it halves the window instead (fast recovery).
- Q4 (disagreement): Reno vs. Cubic vs. BBR disagree on what signal should trigger the
  window's response to congestion at all (packet loss vs. queueing delay).
- Q5 (primary source): Jacobson's 1988 paper frames this entirely as a fix for "congestion
  collapse" observed on the early NSFNET, not as a general performance optimization.
- Q6 (history): the original algorithm assumed loss = congestion; BBR (2016) explicitly
  rejects that assumption in favor of measured bandwidth and round-trip time.

Six questions, five genuinely new atomic claims (Q1 restates more than it adds — that's
fine, not every question pays off every time).

## Worked example — fake deepening (reject this)

Claim: "TCP is a reliable, connection-oriented protocol."

Pass output: "TCP is dependable and connection-based, ensuring reliable delivery of data
over a connection." Same claim, three sentences, zero new atomic facts. A pass producing
output shaped like this against most of its claim list is not deepening — it's padding —
and should be scored at its true new-information rate (near zero), not credited for volume.
