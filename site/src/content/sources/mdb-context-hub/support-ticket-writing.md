---
title: "Support Ticket Writing"
description: "Prose craft for the moment between 'the customer hit a problem' and 'the ticket is closed.' Every word in that window is read by a person who is, by definition, having a worse day than they planned."
---

# Support Ticket Writing

Prose craft for the moment between "the customer hit a problem" and "the ticket is closed." Every word in that window is read by a person who is, by definition, having a worse day than they planned.

## Core Concepts

### 1. The first response is a contract, not a status report

A strong first response always contains four moves, in this order:

1. **Acknowledge** — name the problem in the customer's own words.
2. **Empathize** — name the impact ("I can see how this would block your release"), not a generic "I understand."
3. **Commit** — state what you will do next and *when* you will be back. A timestamp or interval.
4. **Ask only what you need** — batch diagnostic questions; never trickle.

### 2. The "I hear you" plus concrete next step pattern

The most reliable de-escalation move: **acknowledgment of feeling, then a concrete next step.** Either half alone is weaker.

**Strong:**
> I can see how frustrating this is — your cluster has been failing over for three hours and you're heading into a maintenance window. I'm pulling the FTDC now and will reply within 30 minutes either with a root cause or with the questions I need to narrow it down.

The phrase "I understand" is overused to the point of suspicion. "That sounds really frustrating," "I can see why this is urgent" land harder because they're specific.

### 3. Apology calibration

| Cause status | Apology shape |
|---|---|
| Cause confirmed, our fault | Full apology, ownership, remediation, prevention |
| Cause undetermined | Apologize for the experience, not the cause |
| Cause confirmed, customer's environment | Acknowledge impact, do not say "your fault" |
| Cause confirmed, third party | Acknowledge impact, redirect carefully |

Never write "we apologize for any inconvenience this may have caused." It is the most universally-detested phrase in support writing.

### 4. Holding-statement patterns

**A holding statement:**

> "Quick update: I'm still working through the logs you sent. I've ruled out network latency and am now looking at the WiredTiger cache. I'll have a clearer picture by 17:00 UTC. No action needed from you in the meantime."

**The cardinal rule:** never send a holding statement without a next time-boundary.

### 5. Status-update cadence by severity

| Severity | Recommended cadence |
|---|---|
| SEV1 (outage, data loss) | Every 15-30 minutes, even if "no new info" |
| SEV2 (degraded core workflow, no workaround) | Every 1-4 hours during business windows |
| SEV3 (workaround exists) | Once per business day |

### 6. Escalation handoff prose: the warm handoff

**Outgoing owner writes:**
> "I'm bringing in [Name], who specializes in [area], to take over the deep-dive on this. They have the full context — the FTDC, the timeline, what we've ruled out so far. [Name] will reply within [time] with next steps."

**Incoming owner writes within the promised window:**
> "Hi [customer], [outgoing] looped me in. I've read the case and the FTDC; I see what they're describing with the failover loop. Before I dig further, can you confirm: [one or two crisp questions]."

**Anti-pattern:** the incoming owner asks the customer to "summarize what's been happening."

### 7. Phone-the-customer vs ticket-only

**Call the customer when:**
- The case has crossed a sentiment threshold (all-caps, profanity, threats to escalate).
- More than three back-and-forth cycles have occurred without progress.
- The customer is in an active incident.
- The next step requires real-time troubleshooting.
- You're about to escalate up a tier.

**Stay on the ticket when:**
- The technical context benefits from being written.
- Multiple stakeholders need to read the same answer.

**After a phone call, *always* post a summary on the ticket.**

### 8. The closing message

```
Hi [Name],

Confirming the index change resolved the slow queries on the `events` collection.

**Recap for the record:**
- **Symptom:** `find` on `events` with date range filter taking 4-8 seconds.
- **Cause:** missing compound index on `{customer_id: 1, created_at: -1}`.
- **Fix:** index created, queries now use it.

If the slowness recurs, just reply here and the ticket will reopen.
You'll get a short satisfaction survey in the next day or two.

Thanks for the clear repro steps.
```

### 9. The five things to never write

1. **"Please be patient."** Direct command to a person who is out of patience.
2. **"We apologize for any inconvenience this may have caused."** Disbelief plus minimization.
3. **"Per my last email..."** Reads as scolding.
4. **"Unfortunately..."** Lead with the news instead.
5. **"This is a known issue."** Without immediately following it with the workaround, the timeline for a fix, and an apology.

## Templates

### First response on a SEV1

> Hi [Name],
>
> I'm [Your name], picking up this case now. I can see your primary in [cluster] has been unavailable since [time], and your application has been throwing connection errors for [duration]. That's the kind of thing that should never be quiet from us, and I'm sorry you're dealing with it during business hours.
>
> Here's what I'm doing in parallel right now:
> - Pulling the cluster's recent logs and FTDC.
> - Checking the Atlas control-plane status for [region].
>
> I'll reply by [exact time] either with a root cause hypothesis or with the specific diagnostic data I need from you. In the meantime, if the situation changes on your side — for example, the secondary takes over and you regain availability — please let me know.

## Anti-Patterns

- **Generic "I understand"** — use a specific empathy beat instead.
- **Time-vague commitments** — "soon," "shortly," "ASAP." Use clock time in a named timezone.
- **Trickle diagnostics** — asking for one piece of data, waiting, then asking for another.
- **Closing without recap** — no description of cause or fix.
- **Cold handoff** — "I've assigned this to a colleague" with no name, no warm intro.

## References

- [GigaBPO: Customer Service De-escalation Techniques and the HEARD Method](https://gigabpo.com/customer-service-de-escalation/)
- [Supportbench: Customer Update Cadence for Incidents](https://www.supportbench.com/how-to-create-customer-update-cadence-daily-weekly-complex-issues/)
- [Fullview: How To Write a Great Closing Support Ticket Email](https://www.fullview.io/blog/closing-support-ticket-email-templates)
