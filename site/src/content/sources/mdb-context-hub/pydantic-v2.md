---
title: "Pydantic v2 Data Validation and Modeling"
description: "> Reference file — part of the programming-languages hub. Created via /dr research (Pydantic v2 data validation and modeling)."
---

<!-- hub-reference-banner -->
> **Reference file — part of the `programming-languages` hub.** Created via `/dr` research (Pydantic v2 data validation and modeling).
> Sibling topics in this family are reference files under the hubs (`programming-languages`, `software-engineering-patterns`) — **not** standalone
> skills. Ignore any "use the X skill" / `related_skills` / SKIP pointers below that name a bare sibling
> skill; load that topic's `references/<name>.md` from the owning hub (see the hub's "Cross-hub map").
> For general Python idioms, type hints, packaging, and async, see `references/python-patterns.md` in this hub.
> For the TypeScript/JS analog (runtime schema validation), see the top-level `zod-schema-validation` skill.

---
name: pydantic-v2
description: >
  Pydantic v2 expert — runtime data validation and modeling in Python powered by
  the Rust pydantic-core. Covers BaseModel and field definitions (Field, Annotated
  constraints), the three validator modes (field_validator / model_validator,
  before/after/wrap/plain), strict vs lax coercion and ConfigDict, serialization
  (model_dump / model_dump_json, aliases, include/exclude, computed_field, RootModel),
  TypeAdapter for non-model types, discriminated (tagged) unions, pydantic-settings
  (BaseSettings, SettingsConfigDict, env/.env/secrets), ValidationError handling, and
  V1→V2 migration plus performance anti-patterns.
  TRIGGER: defining or validating Pydantic models; field_validator / model_validator;
  Annotated constraints; strict mode / type coercion questions; model_dump / serialization /
  aliases; TypeAdapter; discriminated unions; BaseSettings / config from env; migrating
  Pydantic V1 → V2; Pydantic validation performance tuning.
  SKIP: TypeScript/JS runtime validation — use zod-schema-validation; general Python idioms,
  type hints, packaging, async — use python-patterns.md; pytest/Hypothesis testing —
  use python-testing.md; API/REST design — use software-engineering-patterns.
---

# Pydantic v2 — Data Validation and Modeling in Python

## Overview

Pydantic is the most widely used data-validation library for Python. It validates
data at runtime against Python type hints and produces structured, user-friendly
errors when data is invalid. **Pydantic v2** (released mid-2023, stable and current
through 2026) rewrote the validation/serialization engine in Rust as a separate
package, **`pydantic-core`** (built with PyO3). The result is **~5–50× faster** than
v1 (≈17× on a typical mixed-field model), with the Python layer reduced to schema
*definition* while the hot path runs in compiled Rust.

Three packages make up the ecosystem:
- **`pydantic`** — the Python API (`BaseModel`, `Field`, validators, `TypeAdapter`).
- **`pydantic-core`** — the Rust validation/serialization engine (not used directly).
- **`pydantic-settings`** — `BaseSettings` for config from env vars, `.env`, secrets.

Use it when you need to **parse untrusted input** (API bodies, config, JSON, ORM
rows) into typed Python objects with guarantees, and serialize them back out.

## Core Concepts

### 1. BaseModel and field definitions
Subclass `BaseModel`; annotate fields with type hints. Validation runs on
construction and on the explicit `model_validate*` entry points.

```python
from pydantic import BaseModel, Field
from typing import Annotated

class User(BaseModel):
    id: int
    name: str = "anonymous"                     # default
    tags: list[str] = Field(default_factory=list)  # mutable default → factory
    age: Annotated[int, Field(ge=0, le=130)]    # constraint via Annotated
```

- **Validation entry points:** `User(**data)`, `User.model_validate(dict_or_obj)`,
  `User.model_validate_json(json_str_or_bytes)`. JSON parsing happens *inside Rust*
  in `model_validate_json` — faster than `json.loads()` then `model_validate`.
- **`Field(...)`** carries metadata/constraints: `default`, `default_factory`,
  `alias` / `validation_alias` / `serialization_alias`, `ge/gt/le/lt`,
  `min_length/max_length`, `pattern`, `description`, `frozen`, `exclude`.
- **Prefer `Annotated[type, Field(...)]`** over `field: type = Field(...)` for
  constraints. Constraints inside `Annotated` are compiled into the core schema and
  run in Rust (no Python call overhead). They also compose with `list[...]`,
  `dict[...]`, etc. (e.g. `list[Annotated[int, Field(gt=0)]]`).
- **`from_attributes=True`** (in `model_config`, replaces v1 `orm_mode`) lets
  `model_validate` read attributes off arbitrary objects (e.g. ORM rows).

### 2. Validators — field, model, and the before/after/wrap modes
Pydantic distinguishes **validators** (input → validated value) from **serializers**
(value → output). Validators run in a defined order around the core (Rust) validation.

```python
from pydantic import BaseModel, field_validator, model_validator, ValidationError
from typing_extensions import Self

class Account(BaseModel):
    username: str
    password: str
    password_confirm: str

    @field_validator("username")          # decorate per-field
    @classmethod                          # field_validator is a classmethod
    def no_spaces(cls, v: str) -> str:
        if " " in v:
            raise ValueError("username must not contain spaces")
        return v.lower()

    @model_validator(mode="after")        # whole-model, cross-field
    def passwords_match(self) -> Self:
        if self.password != self.password_confirm:
            raise ValueError("passwords do not match")
        return self
```

**Modes (the most-confused part of Pydantic v2):**
- `mode="before"` — runs on **raw input** *before* core coercion. Receives whatever
  was passed (often a `dict` or `str`); use to reshape/normalize input.
- `mode="after"` — runs on the **already-validated, typed** value. Safest default for
  business rules; you get a real `int`/`str`/submodel, not raw input.
- `mode="wrap"` — most powerful: receives the value **and** a `handler` callable; you
  decide whether/when to call the inner validator and can transform around it.
- `mode="plain"` — terminates validation; your function fully replaces core validation
  for that field (no core coercion runs).

`model_validator(mode="before")` receives the raw input dict for the whole model;
`mode="after"` receives `self` (return `self`). Raise `ValueError` or `AssertionError`
inside a validator and Pydantic wraps it into a `ValidationError`. Validators can
take an `info: ValidationInfo` param for `info.data` (already-validated siblings),
`info.context`, `info.field_name`.

**Reusable validators:** attach a validator to a type once with
`Annotated[str, AfterValidator(func)]` / `BeforeValidator` / `WrapValidator` /
`PlainValidator` — cleaner than repeating `@field_validator` across models.

### 3. Strict vs lax mode and ConfigDict
By default Pydantic is **lax**: it coerces compatible types (`"123"` → `123`,
`"true"` → `True`). **Strict mode** disables coercion and requires exact types.

```python
from pydantic import BaseModel, ConfigDict

class M(BaseModel):
    model_config = ConfigDict(strict=True)   # whole-model strict
    x: int

M.model_validate({"x": "123"})               # raises: str is not a valid int
```

Strictness is layered (most → least specific): per-call `model_validate(..., strict=True)`
> field-level `Field(strict=True)` / `Strict()` annotation > `model_config`.
Common `ConfigDict` keys:
- `strict`, `frozen` (immutable + hashable; replaces v1 `allow_mutation`),
- `extra` = `"ignore"` (default) / `"forbid"` / `"allow"`,
- `validate_assignment=True` (re-validate on attribute set; off by default),
- `from_attributes=True` (ORM reads), `populate_by_name=True` (accept field name
  *and* alias on input; renamed `validate_by_name` in newer versions),
- `str_strip_whitespace`, `use_enum_values`, `arbitrary_types_allowed`,
- `json_schema_extra`, `ser_json_timedelta`, etc.

`model_config` is a **dict** (`ConfigDict(...)`), not the v1 nested `class Config`.

### 4. Serialization — model_dump, JSON, aliases, computed fields
```python
m.model_dump()                  # → dict, Python objects (datetime stays datetime)
m.model_dump(mode="json")       # → dict with JSON-safe values (datetime → str)
m.model_dump_json()             # → JSON str, serialized in Rust (fast)
```
Key options (apply to all three): `include` / `exclude` (sets or nested dicts),
`by_alias=True` (use `serialization_alias`), `exclude_unset` (only fields explicitly
set — great for PATCH semantics), `exclude_defaults`, `exclude_none`,
`round_trip=True`, `warnings="error"`, `context=...`.

- **Custom serializers:** `@field_serializer("foo", mode="plain"|"wrap")` for one
  field; `@model_serializer` for the whole model; `Annotated[T, PlainSerializer(...)]`
  for reusable type-level serialization.
- **`@computed_field`** — expose a derived `@property` in the serialized output:
  ```python
  from pydantic import BaseModel, computed_field
  class Box(BaseModel):
      w: float; h: float
      @computed_field
      @property
      def area(self) -> float:
          return self.w * self.h
  ```
- **`RootModel[T]`** — a model whose top level is *not* an object (e.g.
  `RootModel[list[int]]`, `RootModel[dict[str, User]]`); replaces v1 `__root__`.

### 5. TypeAdapter — validation/serialization without a BaseModel
`TypeAdapter` brings Pydantic's machinery to *any* type — `list[User]`, `dict[str,int]`,
`TypedDict`, dataclasses, unions — without wrapping it in a model. Build the adapter
once (it compiles a core schema) and reuse it.

```python
from pydantic import TypeAdapter
ta = TypeAdapter(list[User])
users = ta.validate_python([{"id": 1}, {"id": 2}])   # list[User]
users = ta.validate_json(raw_bytes)                  # parse + validate in Rust
ta.dump_json(users)                                  # serialize
ta.json_schema()                                     # JSON Schema for the type
```
Use it for bulk validation of homogeneous collections (build the adapter at module
scope, not per call) and for validating request/response bodies that aren't models.

### 6. Discriminated (tagged) unions
Add a `discriminator` so the core validator picks **one** union member by a tag field
instead of trying each — faster, and produces one clean error instead of N.

```python
from typing import Literal, Union, Annotated
from pydantic import BaseModel, Field

class Cat(BaseModel):
    kind: Literal["cat"]; meows: int
class Dog(BaseModel):
    kind: Literal["dog"]; barks: int

class Owner(BaseModel):
    pet: Annotated[Union[Cat, Dog], Field(discriminator="kind")]
```
For tags that aren't a plain field, use a **callable discriminator** via
`Discriminator(func)` — and handle both `dict` and model inputs inside it, since the
callable also runs during serialization. Discriminated unions also emit cleaner
OpenAPI/JSON-Schema. Non-discriminated unions use **smart mode** (best-match) by
default; left-to-right is available but usually worse.

### 7. pydantic-settings — typed configuration
`BaseSettings` populates fields from (priority high→low): **init kwargs → env vars →
`.env` file → secrets dir → field defaults**.

```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_nested_delimiter="__",   # APP_DB__HOST → db.host
        secrets_dir="/run/secrets",
        extra="ignore",
    )
    debug: bool = False
    db: "DbConfig"
```
- **Nested config:** `env_nested_delimiter="__"` maps `APP_DB__HOST` to `db.host`
  (double underscore avoids clashing with names that contain single underscores).
- **Secrets:** `secrets_dir` reads each file as one field's value (Docker/K8s secrets).
- **Customize sources** by overriding `settings_customise_sources` (e.g. add a YAML or
  vault source, reorder priority).
- **Best practice:** `.env` for local dev only, commit a `.env.example` without
  secrets, use real environment variables / secret stores in production.

## Tools / Frameworks

- **FastAPI** — built on Pydantic; request/response models *are* Pydantic models.
  FastAPI ≥0.100 requires Pydantic v2.
- **`bump-pydantic`** — automated V1→V2 codemod (renames `@validator`→`@field_validator`,
  `Config`→`model_config`, `.dict()`→`.model_dump()`, etc.). Run it, then review diffs.
- **`datamodel-code-generator`** — generate Pydantic models from JSON Schema / OpenAPI.
- **`json_schema()` / `model_json_schema()`** — emit JSON Schema (draft 2020-12) for any
  model or `TypeAdapter`, including for discriminated unions.
- **mypy / pyright** — Pydantic ships a mypy plugin; v2 models type-check well with
  both checkers.

## Methodology — choosing the right tool

1. **Validating a whole object with named fields?** → `BaseModel`.
2. **Validating a bare collection / TypedDict / union, no model needed?** → `TypeAdapter`.
3. **Reshaping raw input before typing?** → `@field_validator(mode="before")` or a
   model `mode="before"` validator.
4. **Cross-field business rule on typed data?** → `@model_validator(mode="after")`.
5. **Same validation reused across models/types?** → `Annotated[T, AfterValidator(...)]`.
6. **A union you can tag?** → discriminated union (`Field(discriminator=...)`).
7. **App configuration?** → `BaseSettings` from `pydantic-settings`.
8. **Need exact types, no coercion (e.g. money, ids)?** → `strict=True` (per-field or model).

## Practical Patterns

- **Parse, don't validate-then-pass-dicts:** convert at the boundary
  (`Model.model_validate_json(body)`) and pass typed models inward.
- **PATCH/partial update:** `model_dump(exclude_unset=True)` to send only fields the
  client actually set.
- **Aliases for external naming:** `Field(validation_alias="userId",
  serialization_alias="user_id")`; set `populate_by_name=True` to also accept the
  Python field name on input.
- **Immutable value objects:** `model_config = ConfigDict(frozen=True)` → hashable,
  usable as dict keys / in sets.
- **Bulk validation:** build one module-level `TypeAdapter(list[Model])` and call
  `validate_python` once on the whole batch rather than looping per item.
- **Context-aware validation:** `Model.model_validate(data, context={...})`, read via
  `info.context` in validators (e.g. inject locale, feature flags).

## Anti-Patterns (and the fix)

- **Overusing `@field_validator` for simple bounds.** A Python validator always runs in
  Python (function-call overhead, duplicates checks). → Use `Annotated[int, Field(ge=0)]`
  so the constraint runs in Rust.
- **`mode="before"` when you wanted typed data.** Before-validators get *raw* input
  (often a `str`/`dict`), causing `AttributeError`/type bugs. → Use `mode="after"` for
  rules on validated values.
- **Building a `TypeAdapter` inside a hot loop / per request.** It recompiles the core
  schema each time. → Construct once at module scope and reuse.
- **`json.loads()` then `model_validate(dict)`.** → `model_validate_json(raw)` parses
  and validates in one Rust pass.
- **v1 carry-overs:** `class Config` (→ `model_config = ConfigDict(...)`), `@validator`
  (→ `@field_validator`), `@root_validator` (→ `@model_validator`), `.dict()`
  (→ `.model_dump()`), `.json()` (→ `.model_dump_json()`), `parse_obj` (→ `model_validate`),
  `parse_raw` (→ `model_validate_json`), `from_orm`/`orm_mode`
  (→ `model_validate(obj)` + `from_attributes=True`), `allow_mutation=False`
  (→ `frozen=True`), `each_item=True` (→ annotate the inner type).
- **Mutable default shared across instances** (`tags: list = []`). → `Field(default_factory=list)`.
- **Mixing Pydantic v1 and v2 models** in one validation graph — they don't nest cleanly;
  migrate the whole graph (`bump-pydantic`), or use the `pydantic.v1` shim deliberately.
- **Expecting `validate_assignment` by default.** It's off; set
  `ConfigDict(validate_assignment=True)` if you mutate after construction.

## Troubleshooting

- **`ValidationError`** — iterate `exc.errors()` for structured dicts (`loc`, `msg`,
  `type`, `input`); `exc.json()` / `exc.error_count()` for reporting. The `type`
  string (e.g. `int_parsing`, `missing`, `string_too_short`) is the stable machine key.
- **"Input should be a valid integer" under strict mode** — you passed a string to a
  strict `int`; coerce upstream or drop strictness for that field.
- **Serialization warning "Expected X but got Y"** — a field's runtime value doesn't
  match its declared type (common with `Any`/subclasses); set
  `model_dump(serialize_as_any=True)` for duck-typed/polymorphic output, or fix the type.
- **`PydanticUndefinedAnnotation` / forward refs** — call `Model.model_rebuild()` after
  the referenced type is defined (self-referential or late-bound models).
- **Settings not picked up** — check `env_prefix`, the `env_nested_delimiter`, and that
  `.env` is found (relative to CWD unless an absolute `env_file` path is given).
- **`extra` fields silently dropped** — default is `"ignore"`; use `"forbid"` to catch
  typos in input, `"allow"` to keep them.

## References

- Pydantic official docs — Validation (concepts, API): https://docs.pydantic.dev/latest/
- Pydantic — Migration Guide (V1 → V2): https://docs.pydantic.dev/latest/migration/
- Pydantic — Unions / discriminated unions: https://docs.pydantic.dev/latest/concepts/unions/
- Pydantic — Serialization: https://docs.pydantic.dev/latest/concepts/serialization/
- Pydantic — Strict mode: https://docs.pydantic.dev/latest/concepts/strict_mode/
- Pydantic — Performance: https://docs.pydantic.dev/latest/concepts/performance/
- pydantic-settings — Settings Management: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
- Pydantic v2 announcement (architecture / Rust core): https://pydantic.dev/articles/pydantic-v2
- pydantic-core (Rust engine): https://github.com/pydantic/pydantic-core
- bump-pydantic (V1→V2 codemod): https://github.com/pydantic/bump-pydantic
