# Conditional pricing arithmetic

This record supplies firsthand reproducible arithmetic. Its inputs are explicit
assumptions or attributed amounts. It is not an Atlas benchmark, an invoice,
measured savings, a TCO study or evidence that service scopes are equivalent.
It receives zero independent organization credit.

Run `python3 verify_pricing_math.py`. Normal and `-O` execution must produce the
same JSON. Checks remain enabled under `-O`; Decimal results are replayed with
Fraction independently.

| Calculation | Inputs | Result and boundary |
| --- | --- | --- |
| Monthly headline/cap ratio | 56.94 / 30 | 1.898, approximately 1.9; compare matching periods and charge scopes only |
| Illustrative shared-cluster ratio | 57 / 30 | 1.9; 57 is an explicit modeling assumption |
| Integer fleet threshold | Flex component cap 30 each, shared component 57 | At full caps, 1 cluster gives 30 and 2 give 60. Two is the minimum integer count for a possible saving; it is not sufficient, and aggregate workload must fit |
| Illustrative hourly multiplication | 0.08 × 730 hours | 58.40. Difference from 56.94 is 1.46; this does not explain the vendor headline’s configuration or billing-period basis |
| Reported cash amounts | 3000 → 160 | 94.666666…% lower, approximately 95%. The actual post reports over 3000, so 3000 is an illustrative baseline. Availability, staffing, tax and service scopes are not matched |
| Reported component sum/share | 700 + 1000, divided by 3000 | 1700 and 56.666666…%, approximately 57%. With a total strictly above 3000, the exact share is below 56.666666…% |

For any nonnegative integer N, assume that each included Flex cluster-charge
component c_i satisfies 0 ≤ c_i ≤ 30 for the same period, currency and charge
scope. Adding the N inequalities gives:

`sum(c_i) ≤ sum(30) = 30N`.

Equality requires every included component to reach the cap. This is a
conditional algebraic bound on the stated component; it does not cap an entire
Atlas invoice. The executable checks illustrative fleets, replays their sums
and bounds with Fraction, and rejects a component above the assumed cap.
Those finite examples do not constitute an empirical proof of a universal
statement; the general result follows by adding the component inequalities.

Primary documents must separately establish the applicability of vendor inputs.
MongoDB’s Flex cost guide reports an 8–30 monthly cluster charge range and its
pricing page displays a 56.94 monthly starting headline and 0.08 hourly amount.
These displays alone do not establish identical periods, regions or contracts.
Other Atlas service charges remain separate.

Prosopo reports an Atlas total over 3000, backup 700, internet transfer 1000,
and replacement server 160 in a migration case study. It also describes changing
from a replica set to one server and operating its own backups. The calculation
does not turn that case into a controlled equivalent-service TCO comparison.

Primary-input dependencies:

- [MongoDB Flex cost guide](https://www.mongodb.com/docs/atlas/billing/atlas-flex-costs/)
- [MongoDB pricing](https://www.mongodb.com/pricing)
- [Prosopo’s migration case](https://prosopo.io/blog/we-cut-our-mongodb-costs-by-90-percent/)

Read the pinned versions alongside any claim. These links do not attest that a
future page matches the assumed inputs here.
