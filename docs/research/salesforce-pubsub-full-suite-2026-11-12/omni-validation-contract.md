# Proposed Omni validation contract

Proposed profile; no validator or org check was executed. It uses accepted identity research and [Avro facts](../../../outputs/llms-concepts/salesforce-cdc-avro-schemas-and-changed-field-interpretation.llms/llms-facts.txt). The canonical identity-only diagnostic keeps its optional schema lookup. **The full profile requires schema qualification.**

## Independent dimensions

| Dimension | Proposed PASS condition |
| --- | --- |
| `metadataIdentity` | Channel/member identities, entities and predicates match the approved contract. |
| `topicCapability` | Intended-principal lookup matches topic/tenant and allows subscription; record publishing separately. |
| `schemaCompatibility` | ID-bound schemas cover required entities/members and pass parsing, resolution and field/type checks. |
| `deliverySemantics` | Separate representative tests evidence required member events and predicate behavior. |

Each dimension is `PASS`, `FAIL` or `UNQUALIFIED`. Contradiction/incompatibility is FAIL; missing inputs, unavailable evidence or incomplete extraction is UNQUALIFIED. Require all four PASS for full-profile acceptance.

## Identity and capability inputs

Require contract version, expected channel/tenant, member/entity bindings, predicates and opaque principal-context reference. Enumerate IDs; retrieve `FullName`/`Metadata` per record. Join custom-member `EventChannel` IDs to channel IDs; keep IDs distinct from names. See [channel](https://developer.salesforce.com/docs/platform/api-tooling/references/tooling-objects/tooling-platformeventchannel.html) and [member](https://developer.salesforce.com/docs/platform/api-tooling/references/tooling-objects/tooling-platformeventchannelmember.html) constraints.

Derive the topic from configured full name and CDC naming rule. Preserve [recorded `_chn`/`__chn` and AgentWork conflicts](architecture-assessment.md); never guess. Unresolved identity is UNQUALIFIED. Compare `GetTopic` identity; retain separate `can_subscribe`/`can_publish`, `schema_id` and `rpc_id`. Denied subscription is FAIL; unavailable information is UNQUALIFIED. Status alone cannot identify a permission cause. See [RPC](https://developer.salesforce.com/docs/platform/pub-sub-api/references/methods/gettopic-rpc.html) and [errors](https://developer.salesforce.com/docs/platform/pub-sub-api/guide/handling-errors.html).

## Required schema qualification

1. **Bind identity/applicability.** Require a nonempty ID accepted by the approved client/protocol validator and evidence linking its schema to the assessed entity/member. Never infer entity identity from an Avro record name. Missing validity/applicability rules mean UNQUALIFIED. One channel-level `GetTopic` result cannot certify every member. For received events, use each event message's schema ID from `FetchResponse`; see the Avro facts above.
2. **Retrieve.** Require `GetSchema` or an integrity-checked cache entry for that exact ID and compatible context. Require request/response ID agreement; retain response hash and RPC ID. Empty/invalid or mismatched supplied IDs are FAIL. No applicable ID/schema, or unavailable retrieval, is UNQUALIFIED. Never substitute another schema.
3. **Execute checks.** Run a real Avro parser and writer/reader record-resolution check. Check operator-qualified expected entity structure and every required consumer/predicate path and allowed type. Require expectation provenance; invent no Salesforce type bindings. Predicate paths must exist in the applicable writer structure; reader defaults do not establish source presence. Allow consumer defaults only under the approved reader contract.
4. **Classify.** Parsing/resolution failure, a missing required path or incompatible type in a complete applicable schema is FAIL. Incomplete extraction, unresolved expectations or unproven member coverage is UNQUALIFIED; infer no absence from incomplete material. Schema presence grants no recipient authorization or proof of historical change; retain changed-field decoding rules.

Cache by exact schema ID with response hash, RPC ID, principal-context reference, applicability evidence and retrieval time; no credentials. Bind derived checks to parser/contract versions. Conflicting hashes for one ID are integrity FAIL; do not overwrite. Schema cache hits do not refresh capability evidence.

## Proposed interface and traces

Proposed pseudocode:

```text
result.metadataIdentity = compare_metadata(contract, observations)
result.topicCapability = compare_topic(contract, topic_response)
for binding in contract.required_entity_schemas:
    schema = require_valid_applicable_id_and_GetSchema_or_cache(binding)
    parse_avro_and_resolve_reader_record(schema, binding)
    verify_qualified_paths_and_types(schema, binding)
result.schemaCompatibility = aggregate_binding_results()
result.deliverySemantics = assess_separate_test_evidence()
full_pass = every_dimension_is_PASS(result)
```

Each dimension returns `{state, reasonCodes, evidenceRefs}`. Per-binding schema evidence adds `{entityBindingRef, requestedId, returnedId, responseHash, rpcId, principalContextRef, parserVersion, expectedContractVersion, pathTypeResults}`; retain every required binding.

**Unexecuted acceptance traces:**

| Inputs | Required result |
| --- | --- |
| Identity/capability match; applicable schemas parse, resolve and meet expectations; no delivery evidence | First three PASS; delivery UNQUALIFIED; no full PASS. |
| Complete applicable schema lacks a required predicate path or has incompatible type | Schema FAIL, even if reader defaults allow decoding. |
| Applicable ID/schema absent, retrieval unavailable or member coverage unproven | Schema UNQUALIFIED; no field-absence conclusion. |

Use the `integration-clients` transport/recovery guide and [transport pack](../../../outputs/llms-concepts/salesforce-pub-sub-grpc-subscription-flow-control-and-reconnect.llms/llms.txt) for recovery. No wire calls, decoding or acceptance tests ran here.
