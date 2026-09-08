---
title: "Legal Adjacent Writing"
description: "Reference for drafting legal-adjacent prose that will go to counsel: contracts, disclaimers, privacy notices, breach disclosures, and regulator-facing statements. This skill is craft for drafts, not l"
---

# Legal-Adjacent Writing

Reference for drafting legal-adjacent prose that will go to counsel: contracts, disclaimers, privacy notices, breach disclosures, and regulator-facing statements. This skill is **craft for drafts**, not legal advice. Every output should carry a "counsel must review before execution" footer.

## The five-point legal-adjacent writing test

1. **Is the risk-allocating verb correct?** "Shall," "will," "must," and "may" are not synonyms. Modern drafting prefers "must" over "shall" because "shall" has been litigated into ambiguity.

2. **Are the defined terms actually defined?** Every Capitalized Term should appear once in a Definitions section.

3. **Does the carve-out language survive a hostile read?** "Except for" should be paired with a non-exhaustive list ("including but not limited to") only when you want breadth.

4. **Is the temporal scope explicit?** "In the 12 months preceding the event giving rise to the claim" is unambiguous. "In the prior year" is ambiguous.

5. **Is the notice-and-cure mechanism workable?** If a clause requires "written notice," specify the delivery channel, the recipient, and the cure window.

## Core Concepts

### 1. The risk-allocation architecture

| Risk | Clause type |
|---|---|
| Product fails to do what you said | Warranty |
| Product does what you said but causes harm | Limitation of liability |
| You get sued by a third party because of your product | Indemnification |
| You can't perform because of an Act of God | Force majeure |

### 2. The limitation-of-liability triangle

Three dials:
1. **Cap amount.** Most common SaaS form: "fees paid by Customer in the 12 months preceding the event."
2. **Damages exclusion.** "No indirect, incidental, special, consequential, or punitive damages, including lost profits."
3. **Carve-outs.** Standard market carve-outs: breach of confidentiality, breach of IP indemnification, payment obligations, gross negligence, willful misconduct, death or personal injury.

### 3. The "AS IS" warranty disclaimer

The standard pattern:
```
EXCEPT AS EXPRESSLY SET FORTH IN THIS AGREEMENT, THE SERVICES ARE PROVIDED "AS IS"
AND "AS AVAILABLE," AND PROVIDER MAKES NO REPRESENTATIONS OR WARRANTIES OF ANY KIND,
WHETHER EXPRESS, IMPLIED, STATUTORY, OR OTHERWISE, INCLUDING WITHOUT LIMITATION ANY
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, TITLE, AND
NON-INFRINGEMENT.
```

The all-caps formatting is not stylistic. It is a UCC § 2-316 "conspicuousness" requirement.

### 4. The 8-K Item 1.05 cyber disclosure

The SEC's 2023 cybersecurity rules require public companies to file a Form 8-K within **four business days** of determining that a cybersecurity incident is **material**.

What must be disclosed:
- The **material aspects** of the nature, scope, and timing of the incident
- The **material impact** or reasonably likely material impact on the registrant

**What is NOT required:** specific technical detail about the attack vector, specific detail about cybersecurity systems, or any detail that would impede ongoing remediation.

### 5. GDPR Article 33 — the 72-hour clock

GDPR Article 33 requires controllers to notify the supervisory authority of a personal data breach "without undue delay and, where feasible, not later than 72 hours after having become aware of it."

**Phased notification is explicitly permitted.** Article 33(4) allows you to provide information "in phases without undue further delay."

The notification must include:
- Nature of the breach
- Name and contact details of the DPO
- Likely consequences of the breach
- Measures taken or proposed

### 6. Privacy notice architecture (GDPR / CCPA / CPRA)

Required components under GDPR Article 13/14:
1. Identity and contact details of the controller
2. Purposes of processing and legal basis for each
3. Recipients or categories of recipients
4. Storage period or criteria
5. Data subject rights
6. Right to lodge a complaint with a supervisory authority

## Templates

### Template: Mutual limitation of liability (market-standard SaaS)

```
LIMITATION OF LIABILITY.

(a) Excluded Damages. EXCEPT FOR EXCLUDED CLAIMS, IN NO EVENT WILL EITHER PARTY BE 
LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES.

(b) Liability Cap. EXCEPT FOR EXCLUDED CLAIMS, EACH PARTY'S TOTAL CUMULATIVE
LIABILITY WILL NOT EXCEED THE TOTAL FEES PAID OR PAYABLE BY CUSTOMER IN THE
TWELVE (12) MONTHS PRECEDING THE EVENT GIVING RISE TO THE CLAIM.

(c) Excluded Claims. "Excluded Claims" means: (i) either party's indemnification
obligations; (ii) breach of confidentiality obligations; (iii) Customer's payment
obligations; (iv) either party's gross negligence, willful misconduct, or fraud.
```

## Anti-Patterns

1. **Mixing "shall" and "must" within the same document.** Pick one register.
2. **The "reasonable" undefined.** "Commercially reasonable" should be defined or paired with a benchmark.
3. **Non-conspicuous warranty disclaimers.** A disclaimer that is not in all caps may be ignored under UCC § 2-316.
4. **Promising what you can't deliver in a privacy notice.** "We will never share your data with anyone" creates a contractual representation.
5. **Stuffing technical detail into an 8-K cyber disclosure.** Describe impact, not mechanism.

## Final reminder

> This is draft language only. It is not legal advice. Qualified counsel must review before execution, filing, or public release.

## References

1. SEC, *Cybersecurity Risk Management, Strategy, Governance, and Incident Disclosure* (Form 8-K Item 1.05 final rule, effective Dec 18, 2023)
2. UK ICO, *Personal data breaches: A guide*
3. GDPR Article 33 and 34
4. UCC § 2-316 (conspicuous disclaimer of implied warranties)
