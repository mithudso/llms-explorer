---
title: "TypeScript Decorators"
description: "A lang-js-ts hub reference for the two distinct decorator systems TypeScript ships. They share the @expr syntax and nothing else: different semantics, different signatures, mutually incompatible emit."
---

# TypeScript Decorators — Standard (Stage 3) vs Legacy (experimentalDecorators), Metadata & Migration

A `lang-js-ts` hub reference for the **two distinct decorator systems** TypeScript ships. They share the `@expr` syntax and nothing else: different semantics, different signatures, mutually incompatible emit. The single most important fact: **the `experimentalDecorators` compiler flag toggles the whole semantics** — flag absent ⇒ TC39 Stage 3 *standard* decorators (TS 5.0+); flag present ⇒ *legacy* experimental decorators (TS 1.5-era proposal). For the type system defer to `typescript-expert.md`; for advanced type operators `typescript-advanced-types.md`; for tsconfig `typescript-compiler-config.md`; for *why* decorators can't run under Node's strip-only TS execution `nodejs-typescript-and-runtime-features.md`.

## Overview

Standard decorators are functions called at class-definition time with a uniform `(value, context)` signature; they can replace the decorated value or hook initializers, and they emit plain ES (no `reflect-metadata` dependency). Legacy decorators use kind-specific signatures (`target`, `propertyKey`, `descriptor`/`parameterIndex`), support **parameter decorators** (which Stage 3 still lacks), and — paired with `emitDecoratorMetadata` — feed runtime type info to the dependency-injection ecosystem (Angular, NestJS, TypeORM, class-validator). That DI dependency is exactly why those frameworks **cannot** migrate to standard decorators automatically.

**Version anchors (memorize — they drive "does my TS support X" questions):**

| Feature | Since | Notes |
| --- | --- | --- |
| Legacy decorators (`experimentalDecorators`) | TS 1.5 | opt-in flag; only path before 5.0 |
| `emitDecoratorMetadata` (+`reflect-metadata`) | TS 1.5 | **requires** `experimentalDecorators`; legacy-only |
| `accessor` keyword (auto-accessors) | **TS 4.9** | shipped *before* decorators so 5.0 could target it |
| **Standard** Stage 3 decorators (no flag) | **TS 5.0** | TC39 Stage 3; incompatible with legacy |
| Stage 3 **decorator metadata** (`Symbol.metadata`/`context.metadata`) | **TS 5.2** | needs `lib` `esnext`/`esnext.decorators`, `target` ≤ es2022 |
| Parameter decorators | legacy-only | **no equivalent in Stage 3** (yet) |

## Core Concepts

### 1. How TypeScript picks a system (the flag is a whole-semantics switch)

- **Before TS 5.0**, decorators *required* `"experimentalDecorators": true`; there was no standard option, so a decorator without the flag was an error.
- **TS 5.0+**: `experimentalDecorators` **present/true** ⇒ legacy semantics + legacy type-checking + legacy emit (`__decorate`/`__metadata` helpers). **Absent/false** ⇒ standard Stage 3 semantics + emit.
- They are **not interoperable.** A function written for one signature throws or mis-types under the other. The TS 5.0 notes state the new proposal is "incompatible with `--experimentalDecorators`… and `--emitDecoratorMetadata`… and parameter decorators." You pick one system per project (effectively per `tsconfig`).

### 2. Standard (Stage 3) decorator model — the `(value, context)` signature

Every standard decorator is `(value, context) => replacement | void`. `value` is the thing being decorated (a method/getter/setter function, the class constructor, the `{get,set}` pair for an auto-accessor, or **`undefined` for a plain field**). `context` is a per-kind object:

| Context field | Meaning |
| --- | --- |
| `kind` | `"class"` \| `"method"` \| `"getter"` \| `"setter"` \| `"field"` \| `"accessor"` |
| `name` | `string \| symbol`; for `private`, a readable description only |
| `static` | boolean — static class element (not on `kind:"class"`) |
| `private` | boolean — private element (not on `kind:"class"`) |
| `access` | shape varies: `{ get }` (method/getter), `{ set }` (setter), `{ get, set }` (field/accessor) — lets the decorator read/write the element on an instance |
| `addInitializer(fn)` | queue init logic; runs in the constructor for instance elements (after super, before field inits depending on element), at class-definition time for static |
| `metadata` | the shared metadata object (TS 5.2+; see §6) |

**What each kind may return:**

| Kind | `value` | May return |
| --- | --- | --- |
| `class` | constructor | a **new constructor** (callable) replacing the class, or `void` |
| `method` | the method fn | a **replacement function**, or `void` |
| `getter` | the getter fn | a **replacement getter**, or `void` |
| `setter` | the setter fn | a **replacement setter**, or `void` |
| `field` | `undefined` | an **initializer mutator** `(initialValue) => newValue`, or `void` |
| `accessor` | `{ get, set }` | an object `{ get?, set?, init? }` (omitted = unchanged), or `void` |

A non-conforming return throws (e.g. a method decorator returning a non-function).

```ts
// Standard method decorator (TS 5.0+, NO experimentalDecorators) — fully typed
function logged<This, Args extends any[], Return>(
  target: (this: This, ...args: Args) => Return,
  context: ClassMethodDecoratorContext<This, (this: This, ...args: Args) => Return>
) {
  const name = String(context.name);
  return function (this: This, ...args: Args): Return {
    console.log(`-> ${name}`);
    const result = target.call(this, ...args);
    console.log(`<- ${name}`);
    return result;
  };
}

// Field decorator: value is UNDEFINED; you return an initializer mutator.
function double(_value: undefined, ctx: ClassFieldDecoratorContext<unknown, number>) {
  if (ctx.static || ctx.private) throw new Error("public instance only");
  return (initial: number) => initial * 2;   // runs per-instance against the initializer
}

// addInitializer: auto-bind `this` without touching the method body.
function bound(_v: unknown, ctx: ClassMethodDecoratorContext) {
  const name = ctx.name;
  if (ctx.private) throw new Error("cannot bind private members");
  ctx.addInitializer(function (this: any) { this[name] = this[name].bind(this); });
}

class Person {
  #name = "Ada";
  @double accessor copies = 3;   // -> instance sees 6

  @bound
  @logged
  greet() { console.log(`Hi, I'm ${this.#name}`); }
}
```

### 3. The `accessor` keyword (auto-accessors) — TS 4.9

`accessor x = init` de-sugars to a private backing field plus a `get`/`set` pair on the prototype. It shipped in **TS 4.9** (alongside `satisfies`), deliberately ahead of decorators, so that a `kind:"accessor"` decorator has a uniform `{ get, set }` to wrap and an `init` hook to transform the initial value. Supports `static` and `private` modifiers.

```ts
class Person { accessor name: string = "Ada"; }
// roughly:
class Person {
  #name = "Ada";
  get name() { return this.#name; }
  set name(v: string) { this.#name = v; }
}
```

### 4. Decorator factories & composition

A **factory** is a function returning a decorator — parameterize behavior:

```ts
function logged(prefix = "LOG:") {            // factory
  return function (target: any, ctx: ClassMethodDecoratorContext) {  // the decorator
    const name = String(ctx.name);
    return function (this: any, ...args: any[]) {
      console.log(`${prefix} ${name}`);
      return target.call(this, ...args);
    };
  };
}
class C { @logged("⚠️") run() {} }
```

### 5. Evaluation order vs application order (standard)

Two separate orderings — do not conflate them:

- **Decorator *expressions* are evaluated top-to-bottom, left-to-right** (interspersed with computed property names), and the results stashed.
- **Decorators are *applied* bottom-to-top** on a single element. In `@bound @logged greet()`, `@logged` (innermost/closest to the method) wraps the original first; `@bound` wraps the result. So the *expression* `logged(...)` is evaluated before `bound`, but `logged`'s decorator runs against the raw method and `bound`'s against `logged`'s output.
- **The class decorator runs LAST**, after all method and non-static field decorators have been applied (the new class isn't available until then). **Static field initializers run after** the class decorator. Placement around `export` is allowed on one side only: `@reg export default class {}` or `export default @reg class {}`, never both.

### 6. Metadata — Stage 3 (`Symbol.metadata`) vs legacy (`reflect-metadata`)

**Stage 3 (TS 5.2+, `proposal-decorator-metadata`):** `context.metadata` is a plain object shared by **all** decorators on one class. Decorators write into it; after the class is defined it's exposed as `TheClass[Symbol.metadata]`. No external library, no type reflection — you record what you choose.

```ts
const serializables = new WeakMap<object, string[]>();
function serialize(_t: any, ctx: ClassFieldDecoratorContext | ClassAccessorDecoratorContext) {
  if (ctx.static || ctx.private || typeof ctx.name !== "string")
    throw new Error("public string instance members only");
  let names = serializables.get(ctx.metadata);
  if (!names) serializables.set(ctx.metadata, names = []);
  names.push(ctx.name);
}
function jsonify(instance: object): string {
  const meta = (instance.constructor as any)[Symbol.metadata];
  const names = meta && serializables.get(meta);
  if (!names) throw new Error("nothing marked @serialize");
  return `{ ${names.map(k => `${JSON.stringify(k)}: ${JSON.stringify((instance as any)[k])}`).join(", ")} }`;
}
// Polyfill (most runtimes lack it): Symbol.metadata ??= Symbol("Symbol.metadata");
// tsconfig: target <= es2022, lib includes "esnext" or "esnext.decorators".
```

**Legacy (`emitDecoratorMetadata` + `reflect-metadata`):** when both `experimentalDecorators` and `emitDecoratorMetadata` are on, `tsc` **emits design-time type metadata** for *decorated* declarations, readable via `reflect-metadata`'s `Reflect.getMetadata`:

- `design:type` — the type of a property/accessor.
- `design:paramtypes` — the constructor/method parameter types (**the basis of DI auto-wiring**).
- `design:returntype` — a method's return type.

This is what powers `@Injectable()`/constructor injection: the framework reads `design:paramtypes` to know what to inject. **Stage 3 has no equivalent** — it records no types and has no parameter decorators.

### 7. Legacy decorator signatures (still in heavy use)

| Legacy kind | Signature | Return |
| --- | --- | --- |
| Class | `(target: Function)` | optional **replacement constructor** (you must preserve the prototype yourself) |
| Method | `(target, propertyKey, descriptor: PropertyDescriptor)` | optional replacement `PropertyDescriptor` |
| Accessor | `(target, propertyKey, descriptor)` | optional descriptor — **decorate only the *first* `get`/`set` of a member** (one descriptor covers both) |
| Property | `(target, propertyKey)` | **ignored** — no descriptor arg, can only *observe* the declaration |
| **Parameter** | `(target, propertyKey, parameterIndex: number)` | **ignored** — observe-only; **Stage 3 has none** |

`target` = the prototype for instance members, the constructor for static members.

```ts
// LEGACY (requires "experimentalDecorators": true)
import "reflect-metadata";

function sealed(constructor: Function) {            // class decorator
  Object.seal(constructor); Object.seal(constructor.prototype);
}
function enumerable(value: boolean) {               // method-decorator factory
  return (target: any, key: string, desc: PropertyDescriptor) => { desc.enumerable = value; };
}
const requiredKey = Symbol("required");
function required(target: Object, key: string | symbol, index: number) { // PARAMETER decorator (legacy-only)
  const existing: number[] = Reflect.getOwnMetadata(requiredKey, target, key) || [];
  existing.push(index); Reflect.defineMetadata(requiredKey, existing, target, key);
}

@sealed
class BugReport {
  @enumerable(false) toString() { return "report"; }
  print(@required verbose: boolean) {}
}
```

**Legacy evaluation order** (distinct from the standard rule in §5) — TS Handbook "Decorator Evaluation":
1. Parameter decorators, then Method/Accessor/Property decorators, for **each instance member**.
2. Parameter decorators, then Method/Accessor/Property decorators, for **each static member**.
3. Parameter decorators for the **constructor**.
4. **Class decorators** for the class.
(Within one member, expressions evaluate top-to-bottom, functions are called bottom-to-top — same composition rule as standard.)

## Tools / Frameworks

- **TypeScript 5.0+** — standard decorators by default; `experimentalDecorators` for legacy.
- **`reflect-metadata`** — runtime metadata store for the *legacy* `emitDecoratorMetadata` path; the foundation of DI auto-wiring.
- **Angular (16+), NestJS (10+), TypeORM (0.3+), class-validator, TypeGraphQL, MikroORM, routing-controllers** — all on **legacy** decorators + `emitDecoratorMetadata`. They rely on `design:paramtypes` (DI) and/or parameter decorators, neither of which exists in Stage 3.
- **tsx / ts-node / swc / esbuild / Babel** — runners/transpilers that can emit either system's helper code (esbuild supports legacy decorators; standard support varies by tool/version).

## Methodology

1. **Pick a system per project.** New code with no DI-framework constraint → **standard** (no flag) — it's ECMAScript-aligned and library-free. Code on Angular/NestJS/TypeORM/class-validator → **stay legacy** (`experimentalDecorators` + `emitDecoratorMetadata` + `reflect-metadata`).
2. **For standard decorators**, write `(value, context)`, branch on `context.kind`, guard `static`/`private`, and return the correct shape per kind (esp. the field *initializer mutator* and the accessor `{get,set,init}` object).
3. **For metadata**, choose by system: Stage 3 `context.metadata`/`Symbol.metadata` (TS 5.2+, record-what-you-choose) vs legacy `reflect-metadata` + `design:*` (auto type reflection).
4. **Never mix systems** in one compilation; the flag flips global semantics.

## Practical Patterns

- **Method wrapping (standard):** return a replacement fn from a `method` decorator; use a factory for parameters.
- **Auto-bind:** `addInitializer(function(){ this[name] = this[name].bind(this); })` in a `method` decorator — no body edit.
- **Field transform:** `field` decorator returns `(initial) => transformed`; `value` is `undefined`.
- **Mark-and-collect:** write member names into `context.metadata`; read via `instance.constructor[Symbol.metadata]` (Stage 3 serialization/validation).
- **Legacy DI:** `@Injectable()` class decorator + constructor params whose types `tsc` emits as `design:paramtypes`; the container reads them with `reflect-metadata`.

## Anti-Patterns

- **Reusing a legacy decorator under the standard system (or vice versa).** Signatures differ (`target, propertyKey, descriptor` vs `value, context`); it throws or mis-types. Convert deliberately.
- **Expecting standard decorators to give you parameter metadata / DI.** No parameter decorators, no `design:paramtypes` in Stage 3. Don't try to port a NestJS/Angular DI app to standard decorators expecting injection to keep working.
- **Treating a `field` decorator's `value` as the field value.** It's `undefined`; transform via the returned `(initial) => …` mutator.
- **Decorating both `get` and `set` of a legacy accessor.** Apply to the first accessor in document order only — one `PropertyDescriptor` covers both.
- **Returning a legacy class-replacement constructor without preserving the prototype** — the runtime won't do it for you.
- **Assuming standard decorators run after Node's native type-strip.** Decorators aren't type-only syntax — legacy emits `__decorate` runtime helpers (needs `tsc`/`tsx`/swc/Babel); standard needs engine support V8 hasn't shipped. So `.ts` with decorators won't run under Node's strip-only path. (Deep mechanics → `nodejs-typescript-and-runtime-features.md`.)
- **Enabling `emitDecoratorMetadata` without `experimentalDecorators`** — it's legacy-only and has no effect in the standard system.

## Troubleshooting

- **Decorator "not callable" / wrong-arity errors after a TS 5.0 upgrade** → you removed `experimentalDecorators` and your decorators are legacy-shaped. Re-add the flag or rewrite to `(value, context)`.
- **DI stops resolving / `Cannot resolve dependencies` in NestJS/Angular** → `experimentalDecorators` or `emitDecoratorMetadata` got turned off, or `import "reflect-metadata"` is missing from the entrypoint. Restore all three.
- **`Symbol.metadata` is `undefined` at runtime** → missing polyfill (`Symbol.metadata ??= Symbol("Symbol.metadata")`) and/or `lib` lacks `esnext.decorators`; needs TS 5.2+ and `target` ≤ es2022.
- **`context.metadata` is `undefined`** → TS < 5.2, or you're on the legacy system (legacy decorators have no `context`).
- **A parameter decorator "doesn't exist" under standard decorators** → correct; Stage 3 has none. Keep that file on legacy or move the concern to a method/class decorator.
- **Property decorator return ignored (legacy)** → by design; property decorators can only observe, not modify. Use a method/accessor decorator or `accessor` + standard.

## References

- TypeScript 5.0 — Decorators: https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-0.html
- TypeScript 5.2 — Decorator Metadata: https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-2.html
- TypeScript 4.9 — Auto-Accessors in Classes: https://www.typescriptlang.org/docs/handbook/release-notes/typescript-4-9.html
- TS Handbook — Decorators (legacy/experimentalDecorators): https://www.typescriptlang.org/docs/handbook/decorators.html
- TSConfig — emitDecoratorMetadata: https://www.typescriptlang.org/tsconfig/emitDecoratorMetadata.html
- TC39 — proposal-decorators (Stage 3): https://github.com/tc39/proposal-decorators
- TC39 — proposal-decorator-metadata: https://github.com/tc39/proposal-decorator-metadata
- TypeORM #10869 (legacy→standard decorator migration discussion): https://github.com/typeorm/typeorm/issues/10869
