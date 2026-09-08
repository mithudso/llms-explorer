---
title: "Policy and Governance Writing"
description: "Policies prescribe. They do not propose, persuade, or describe — they bind. A reader of a policy needs three things in the first 60 seconds: who is bound by it, what they must do, and what happens if"
---

# Policy and Governance Writing

## Overview

Policies prescribe. They do not propose, persuade, or describe — they bind. A reader of a policy needs three things in the first 60 seconds: who is bound by it, what they must do, and what happens if they don't.

## Core Concepts

### 1. RFC 2119 / RFC 8174 normative keywords (BCP 14)

| Keyword | Meaning |
|---|---|
| MUST / REQUIRED / SHALL | Absolute requirement |
| MUST NOT / SHALL NOT | Absolute prohibition |
| SHOULD / RECOMMENDED | Strong default — deviation requires documented reason |
| SHOULD NOT / NOT RECOMMENDED | Strong default against |
| MAY / OPTIONAL | Truly optional |

**RFC 8174 clarification:** The normative meaning attaches only when the keyword is in ALL CAPITALS. Lowercase "must", "should", and "may" carry their normal English meaning and have no normative weight.

**Required incantation:**
> The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in BCP 14 [RFC2119] [RFC8174] when, and only when, they appear in all capitals, as shown here.

### 2. The policy / standard / procedure / guideline hierarchy (NIST SP 800-12)

- **Policy** — *what* must be true, and *why*. Mandatory. Strategic. Changes rarely.
- **Standard** — *which* specific implementation satisfies the policy (TLS 1.3, AES-256). Mandatory. Tactical.
- **Procedure** — *how* to perform a specific task. Mandatory for the role performing the task. Operational.
- **Guideline** — *suggested* approach when no mandatory standard applies. Advisory.

**The hierarchy test:** if you can answer "yes" to "would this need to change when we upgrade the firewall?", it is not a policy. It is a standard or procedure.

### 3. Required components of an enforceable policy

1. **Title and identifier** — unique policy ID, version number, effective date
2. **Purpose** — one-paragraph statement of why the policy exists
3. **Scope** — who, what, where the policy applies; explicit in-scope and out-of-scope lists
4. **Definitions** — every term of art, listed alphabetically
5. **Policy statements** — the normative rules, using BCP 14 keywords in ALL CAPS
6. **Roles and responsibilities** — named role titles (not individuals) mapped to obligations
7. **Exceptions** — how to request and approve a documented deviation
8. **Enforcement** — consequences of violation
9. **Related documents** — pointers to standards, procedures, and laws
10. **Review schedule** — review cadence, owner, next review date, change-history table

### 4. The scope section as the contract boundary

A defensible scope section answers:
- **People** — which employees, contractors, vendors, partners, customers?
- **Assets** — which systems, data classifications, networks, locations, devices?
- **Activities** — which operations, transactions, or behaviors?

State each as an inclusion list AND an exclusion list.

### 5. The exception clause

A well-built exception clause has four elements:
1. **Who can grant** — the approval authority (named role, not person)
2. **What must be documented** — business justification, compensating controls, scope, duration
3. **How long it lasts** — maximum duration before re-review (typically 90 or 180 days)
4. **How it is tracked** — where the exception register lives

### 6. Review schedule and change management

ISO/IEC 27001 clause 7.5.3 requires that documents be reviewed and updated as necessary.

- **Review cadence** — at least annual
- **Document owner** — the role accountable for triggering review
- **Change-history table** — a row per version showing version, date, author, change summary, approver

## Policy document skeleton (Markdown)

```markdown
# [Policy Title]

| Policy ID | Version | Effective | Supersedes | Owner | Approver |
|---|---|---|---|---|---|
| POL-NNN | 1.0 | YYYY-MM-DD | n/a | [Role] | [Role] |

## 1. Purpose
[One paragraph: why this policy exists.]

## 2. Scope
**In scope:** [people, assets, activities]
**Out of scope:** [explicit exclusions]

## 3. Definitions
- **Term** — definition.

## 4. Normative Language
[BCP 14 incantation]

## 5. Policy Statements
5.1 [Role] MUST [behavior].
5.2 [Role] MUST NOT [prohibition].
5.3 [Role] SHOULD [strong default]. Deviation requires documented exception per Section 7.

## 6. Roles and Responsibilities
## 7. Exceptions
## 8. Enforcement
## 9. Related Documents
## 10. Review and Change History
```

## Anti-Patterns

1. **The descriptive policy** — lots of background, no rules.
2. **Lowercase normatives** — using "should" and "must" in lowercase while believing they bind readers.
3. **The grab-bag scope** — "This policy applies to everyone and everything." Unenforceable.
4. **Personal-name responsibilities** — "Jane Smith MUST approve all exceptions." Jane leaves; policy breaks.
5. **No exception path** — forces operators to violate or route around.
6. **Procedure leakage** — step-by-step instructions inside a policy.
7. **The standard masquerading as policy** — "All servers MUST run TLS 1.3." When TLS 1.4 ships, the policy is wrong.

## References

1. **RFC 2119** — https://datatracker.ietf.org/doc/html/rfc2119
2. **RFC 8174** — https://www.rfc-editor.org/rfc/rfc8174.html
3. **NIST SP 800-12 Rev. 1** — https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-12r1.pdf
4. **Plain Writing Act of 2010** — https://www.plainlanguage.gov/guidelines/
5. **ISO/IEC 27001:2022** — Information security management systems — Requirements.
