<!-- hub-reference-banner -->
> **Reference file — part of `document-formats` hub.** Formerly standalone `json-advanced` skill.
> Sibling topics now reference files under hubs (`document-formats`) — **not** standalone skills. Ignore "use X skill" / `related_skills` / SKIP pointers naming bare sibling skills; load `references/<name>.md` from owning hub (see hub's "Cross-hub map").

---

---
name: json-advanced
title: "Advanced JSON Patterns"
description: >
  Advanced JSON beyond parse/stringify — streaming parsers, JSON Schema validation (Ajv/Draft 2020-12), JSON Patch (RFC 6902), JSONPath, binary formats (BSON/MessagePack/CBOR), perf optimization (simdjson, fast-json-stringify), NDJSON/JSON Lines, JSON5/JSONC, type-safe validation (Zod/TypeBox).
  TRIGGER: stream large JSON (>100MB), validate with Ajv/Zod, apply JSON Patch/diff, query with JSONPath/JMESPath, serialize faster than JSON.stringify, parse JSON5/JSONC configs, use MessagePack/CBOR, handle BigInt/circular refs/undefined.
  SKIP: basic JSON.parse/JSON.stringify with no advanced needs; JSON in specific framework (use react-nextjs or software-engineering-patterns).
category: developer
version: "1.1.1"
updated: "2026-05-31"
tags: [json, schema-validation, streaming, serialization, node, typescript]
keywords:
  - JSON streaming parser stream-json
  - JSON Schema Ajv Draft 2020-12
  - JSON Patch RFC 6902 fast-json-patch
  - JSONPath jsonpath-plus
  - fast-json-stringify schema serializer
  - MessagePack msgpackr CBOR
  - NDJSON JSON Lines jsonl
  - JSON5 JSONC jsonc-parser
  - Zod TypeBox type-safe validation
  - BigInt circular reference JSON
whenToUse:
  - Stream large JSON not fitting in memory (stream-json, oboe.js)
  - Validate JSON structure against schema (Ajv, Zod, TypeBox)
  - Apply structural diffs/patches to JSON (JSON Patch RFC 6902)
  - Query nested JSON with path expressions (JSONPath, JMESPath)
  - Optimize JSON serialization perf (fast-json-stringify, simdjson)
  - Parse JSON5/JSONC configs with comments and trailing commas
  - Use binary JSON formats (MessagePack, CBOR, BSON) instead of text JSON
  - Handle BigInt, circular refs, undefined, Date round-trips in JSON
whenNotToUse:
  - Basic JSON.parse/JSON.stringify with no advanced needs
  - Framework-specific JSON (use react-nextjs or express-patterns)
  - MongoDB BSON document design (use mongodb-expert or mongodb-schema-design)
related_skills:
  - programming-languages
  - software-engineering-patterns
  - mongodb-expert
---

# Advanced JSON Patterns

Expert reference for JSON beyond `JSON.parse`/`JSON.stringify`. Correct response picks right library for constraint (size, streaming, type safety, binary), flags edge cases (BigInt, circular refs, Date round-trips), produces idiomatic Node.js/TypeScript patterns.

> **Staleness note:** Library versions (Ajv Draft 2020-12, Zod, fast-json-stringify, msgpackr) and benchmarks current as of May 2026. Verify from npm before using.

**Navigation by task:**
- Stream large JSON without loading into memory → JSON Streaming / Large Files
- Validate JSON structure at runtime → JSON Schema (Ajv) or Type-Safe Validation (Zod/TypeBox)
- Apply diffs/patches → JSON Patch (RFC 6902) / JSON Merge Patch
- Query nested structures with path expressions → JSONPath
- Serialize faster than JSON.stringify → Performance Optimization (fast-json-stringify, simdjson)
- Parse JSON5/JSONC configs with comments → JSON5 / JSONC / JSON Lines
- Use binary serialization instead of JSON → Binary JSON Formats (MessagePack, CBOR, BSON)
- TypeScript-native validation with type inference → Type-Safe JSON Validation (Zod, TypeBox)
- Common pitfalls and safe alternatives → Anti-Patterns / Troubleshooting

## Overview

JSON beyond `JSON.parse`/`JSON.stringify` — streaming parsers for large files, schema validation, structural diffing/patching, querying nested data, binary formats, perf optimization. Node.js/JavaScript focus; Python equivalents where relevant.

---

## Core Concepts

### JSON Streaming / Large Files

Files too large for memory (>100MB): use streaming parsers emitting events or objects incrementally.

**Node.js libraries:**

| Library | Style | Use Case |
|---------|-------|----------|
| `stream-json` | Transform streams | Preferred — composable, backpressure-aware |
| `JSONStream` | Event emitter | Legacy but widely used |
| `clarinet` | SAX-style events | Low-level, fastest raw parsing |
| `oboe.js` | Pattern matching | Browser + Node, HTTP streaming |
| `@streamparser/json` | Modern streams | TypeScript-first, Web Streams API |

```javascript
// stream-json: pick specific paths from a large file
const { parser } = require('stream-json');
const { pick } = require('stream-json/filters/Pick');
const { streamArray } = require('stream-json/streamers/StreamArray');
const pipeline = require('stream/promises').pipeline;

await pipeline(
  fs.createReadStream('huge.json'),
  parser(),
  pick({ filter: 'results' }),
  streamArray(),
  async function* (source) {
    for await (const { value } of source) {
      yield processItem(value);
    }
  }
);
```

**NDJSON / JSON Lines (.jsonl):**
One JSON object per line, newline-delimited. Ideal for logs, streaming APIs, append-only files.

```javascript
const readline = require('readline');
const rl = readline.createInterface({ input: fs.createReadStream('data.jsonl') });
for await (const line of rl) {
  const obj = JSON.parse(line);
}

// Writing NDJSON
for (const item of items) {
  stream.write(JSON.stringify(item) + '\n');
}
```

**Python:** `ijson` (streaming), `jsonlines` (NDJSON), `orjson` (fast parse/serialize).

---

### JSON Schema (Draft 2020-12)

Runtime validation of JSON structure and values. Standard for API contracts, config validation, OpenAPI specs.

**Ajv (Node.js) — fastest JSON Schema validator:**

```javascript
const Ajv = require('ajv/dist/2020');
const addFormats = require('ajv-formats');

const ajv = new Ajv({ allErrors: true, coerceTypes: true });
addFormats(ajv);

const schema = {
  $schema: 'https://json-schema.org/draft/2020-12/schema',
  type: 'object',
  properties: {
    email: { type: 'string', format: 'email' },
    age: { type: 'integer', minimum: 0, maximum: 150 },
    role: { type: 'string', enum: ['admin', 'user', 'viewer'] },
    tags: { type: 'array', items: { type: 'string' }, uniqueItems: true }
  },
  required: ['email', 'role'],
  additionalProperties: false
};

const validate = ajv.compile(schema);
if (!validate(data)) console.error(validate.errors);
```

**Key Draft 2020-12 features:** `$dynamicRef`, `prefixItems` (replaces `items` array form), `$vocabulary`, improved `unevaluatedProperties`.

**Schema generation from TypeScript:** `typescript-json-schema`, `ts-json-schema-generator`, `@sinclair/typebox` (runtime + compile-time).

---

### JSON Patch (RFC 6902)

Describes changes to JSON document as array of operations. Used for collaborative editing, API partial updates, audit trails.

```javascript
const jsonpatch = require('fast-json-patch');

const original = { name: 'Alice', age: 30, address: { city: 'NYC' } };
const modified = { name: 'Alice', age: 31, address: { city: 'LA' }, role: 'admin' };

// Generate patch
const patch = jsonpatch.compare(original, modified);
// [{ op: 'replace', path: '/age', value: 31 },
//  { op: 'replace', path: '/address/city', value: 'LA' },
//  { op: 'add', path: '/role', value: 'admin' }]

// Apply patch
const result = jsonpatch.applyPatch(original, patch).newDocument;

// Validate patch before applying
const errors = jsonpatch.validate(patch, original);
```

**Operations:** `add`, `remove`, `replace`, `move`, `copy`, `test`.

**JSON Merge Patch (RFC 7396):** Simpler alternative — send partial object. `null` means delete.
```javascript
const mergePatch = require('json-merge-patch');
const result = mergePatch.apply(original, { age: 31, address: null });
```

---

### JSONPath

Query language for JSON (like XPath for XML). Extract values from deeply nested structures.

```javascript
const { JSONPath } = require('jsonpath-plus');

const data = {
  store: { books: [
    { title: 'A', price: 10, author: 'X' },
    { title: 'B', price: 25, author: 'Y' }
  ]}
};

JSONPath({ path: '$.store.books[*].title', json: data });
// ['A', 'B']

JSONPath({ path: '$.store.books[?(@.price > 15)]', json: data });
// [{ title: 'B', price: 25, author: 'Y' }]

JSONPath({ path: '$..author', json: data });  // recursive descent
// ['X', 'Y']
```

**Common expressions:**
- `$` — root
- `..` — recursive descent
- `[*]` — all elements
- `[?(@.x > 5)]` — filter
- `[0:3]` — slice

**Alternative:** `jmespath` — more predictable than JSONPath, used by AWS CLI.

---

### Performance Optimization

| Library | Purpose | Speed vs JSON.parse |
|---------|---------|-------------------|
| `simdjson` (via `simdjson-js`) | SIMD-accelerated parsing | 2-4x faster on large docs |
| `fast-json-stringify` | Schema-based serialization | 2-10x faster than JSON.stringify |
| `fast-json-parse` | Safe parse (no try/catch) | Same speed, no exception overhead |
| `orjson` (Python) | Rust-based JSON | 3-10x faster than stdlib json |
| `ujson` (Python) | C extension | 2-4x faster parse |

```javascript
// fast-json-stringify — compile a serializer from schema
const fastJson = require('fast-json-stringify');
const stringify = fastJson({
  type: 'object',
  properties: {
    id: { type: 'integer' },
    name: { type: 'string' },
    timestamp: { type: 'string', format: 'date-time' }
  }
});
const json = stringify({ id: 1, name: 'test', timestamp: new Date().toISOString() });
```

**Gotchas:**
- `JSON.parse` throws on trailing commas, comments, `undefined` → use JSON5 for config files
- `BigInt` not serializable → use `replacer`/`reviver` or `json-bigint`
- Circular references crash → use `flatted` or `safe-stable-stringify`
- `Date` serializes to ISO string, doesn't round-trip → use reviver

---

### JSON5 / JSONC / JSON Lines

| Format | Extension | Key Difference |
|--------|-----------|---------------|
| JSON5 | `.json5` | Comments, trailing commas, unquoted keys, hex, Infinity/NaN |
| JSONC | `.jsonc` | JSON + `//` and `/* */` comments only (VS Code, tsconfig) |
| JSON Lines | `.jsonl` | One JSON value per line, no wrapping array |

```javascript
const JSON5 = require('json5');
const config = JSON5.parse(fs.readFileSync('config.json5', 'utf8'));

// JSONC (strip comments then parse)
const { parse } = require('jsonc-parser');
const tsconfig = parse(fs.readFileSync('tsconfig.json', 'utf8'));
```

---

### Binary JSON Formats

| Format | Library (Node) | When to Use |
|--------|---------------|-------------|
| BSON | `bson` (MongoDB driver) | MongoDB wire protocol, rich types (ObjectId, Decimal128, Date) |
| MessagePack | `msgpackr` / `@msgpack/msgpack` | Compact binary, 30-50% smaller than JSON, fast |
| CBOR | `cbor-x` / `cbor` | IETF standard (RFC 8949), self-describing, schema-less |
| Protocol Buffers | `protobufjs` | Schema-required, smallest wire size, gRPC |

```javascript
// MessagePack — drop-in replacement for JSON
const { pack, unpack } = require('msgpackr');
const binary = pack({ name: 'test', values: [1, 2, 3] });
const obj = unpack(binary);
// ~40% smaller than JSON.stringify equivalent

// BSON
const { serialize, deserialize } = require('bson');
const bsonBuffer = serialize({ _id: new ObjectId(), ts: new Date() });
```

**Decision guide:** JSON for human readability + debugging. MessagePack for size-sensitive IPC/caching. BSON for MongoDB. Protobuf for typed RPC contracts.

---

### Type-Safe JSON Validation (Runtime)

Beyond JSON Schema — TypeScript-native validation with type inference.

| Library | Approach | Strengths |
|---------|----------|-----------|
| Zod | Fluent builder API | Best DX, `.parse()` throws, `.safeParse()` returns Result |
| TypeBox | JSON Schema compatible | Generates both TS types AND JSON Schema from one def |
| io-ts | Functional (fp-ts) | Codec pattern, encode + decode |
| Valibot | Tree-shakeable | Smallest bundle, modular validators |
| Arktype | Type syntax in strings | Most concise definitions |

```typescript
// Zod
import { z } from 'zod';
const UserSchema = z.object({
  email: z.string().email(),
  age: z.number().int().min(0).max(150),
  role: z.enum(['admin', 'user', 'viewer']),
  tags: z.array(z.string()).default([])
});
type User = z.infer<typeof UserSchema>;
const user = UserSchema.parse(untrustedInput);

// TypeBox — generates JSON Schema at runtime
import { Type, Static } from '@sinclair/typebox';
import { Value } from '@sinclair/typebox/value';
const T = Type.Object({
  email: Type.String({ format: 'email' }),
  age: Type.Integer({ minimum: 0 })
});
type T = Static<typeof T>;
const valid = Value.Check(T, data);
```

---

## Anti-Patterns

| Anti-Pattern | Why It Fails | Correct Approach |
|---|---|---|
| `JSON.parse` in try/catch for validation | Only catches syntax errors, not schema | Use Ajv or Zod for structural validation |
| Storing large arrays as single JSON files | Can't stream-read, OOM on large data | Use NDJSON (.jsonl) — one object per line |
| `eval()` or `new Function()` for JSON with comments | Code injection vulnerability | Use `json5` or `jsonc-parser` |
| Deep-cloning via `JSON.parse(JSON.stringify(x))` | Loses Date, undefined, functions, symbols | Use `structuredClone()` (Node 17+) |
| Stringify + string replace for "patching" | Fragile, can corrupt nested values | Use JSON Patch (RFC 6902) |
| Ignoring `__proto__` in parsed objects | Prototype pollution attack vector | Use `Object.create(null)` or Ajv's `removeAdditional` |
| Sorting keys manually for deterministic output | Inconsistent, misses nested objects | Use `safe-stable-stringify` or `fast-json-stable-stringify` |

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `SyntaxError: Unexpected token` | BOM, trailing comma, or comment in JSON | Strip BOM, use JSON5 for config, or validate with `jsonlint` |
| `RangeError: Maximum call stack` | Circular reference in object | Use `flatted` or `safe-stable-stringify` |
| Numbers lose precision (>2^53) | JavaScript number limits | Use `json-bigint` with `{ storeAsString: true }` |
| Schema validates but TypeScript types don't match | Schema and type definitions diverge | Use TypeBox (single source of truth) or Zod |
| Streaming parser emits wrong structure | Missing `pick()` filter or wrong path | Log emitted events to debug path expectations |
| `undefined` values disappear after stringify | `JSON.stringify` drops undefined by spec | Use `null` explicitly, or custom replacer |
| NDJSON file corrupts on concurrent writes | Partial line writes interleave | Use file locks (`proper-lockfile`) or append atomically |
| Ajv performance degrades on complex schemas | `$ref` resolution or `allOf` explosion | Precompile schemas, avoid deep `$ref` chains |

---

## References

- [JSON Schema — Official Specification](https://json-schema.org/draft/2020-12/json-schema-core)
- [Ajv — JSON Schema Validator](https://ajv.js.org/) — fastest, Draft 2020-12 support
- [stream-json — npm](https://www.npmjs.com/package/stream-json) — composable streaming
- [fast-json-patch — npm](https://www.npmjs.com/package/fast-json-patch) — RFC 6902
- [jsonpath-plus — npm](https://www.npmjs.com/package/jsonpath-plus) — extended JSONPath
- [fast-json-stringify — npm](https://www.npmjs.com/package/fast-json-stringify) — schema-based serializer
- [Zod — Documentation](https://zod.dev/) — TypeScript-first validation
- [TypeBox — GitHub](https://github.com/sinclairzx81/typebox) — JSON Schema + TS types
- [MessagePack — msgpackr](https://www.npmjs.com/package/msgpackr) — fastest MessagePack for Node
- [JSON Lines spec](https://jsonlines.org/) — NDJSON format specification
- [orjson — Python](https://github.com/ijl/orjson) — fast JSON for Python
- [jmespath — npm](https://www.npmjs.com/package/jmespath) — JMESPath query language