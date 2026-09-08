---
title: "TypeScript Advanced Types"
description: "Expert reference for TypeScript's advanced type system. Covers conditional types, mapped types, branded/nominal types, type narrowing, generic constraints, variadic tuples, template literal types, uti"
---

# TypeScript Advanced Types

Expert reference for TypeScript's advanced type system. Covers conditional types, mapped types, branded/nominal types, type narrowing, generic constraints, variadic tuples, template literal types, utility type internals, and type-level performance.

## When to use this skill

- Writing or reviewing generic type definitions, conditional types, or mapped types
- Implementing branded/nominal types for domain safety
- Debugging "Type instantiation is excessively deep" or union explosion errors
- Designing type-safe builder patterns, event emitters, or state machines
- Choosing between `satisfies`, type annotations, and type assertions
- Optimizing slow type checking in large codebases

## When NOT to use this skill

- General TypeScript project setup, tsconfig, module resolution -- use `typescript-expert`
- Runtime validation with Zod/io-ts -- use `zod-schema-validation`
- Framework-specific typing (React, Express, etc.) -- use the framework skill
- Pure JavaScript without TypeScript types

## Scope boundary

This skill covers the TYPE SYSTEM exclusively. For general TypeScript project setup, runtime patterns, module resolution, or framework integration, use the `typescript-expert` skill instead.

---

## 1. Conditional Types and `infer`

### Basic conditional types

```typescript
// Syntax: T extends U ? X : Y
type IsString<T> = T extends string ? true : false;

type A = IsString<"hello">;  // true
type B = IsString<42>;       // false
```

### Distributive conditional types

When the checked type is a **naked type parameter**, the conditional distributes over union members individually.

```typescript
type ToArray<T> = T extends unknown ? T[] : never;

// Distributes: string[] | number[]  (NOT (string | number)[])
type Result = ToArray<string | number>;
```

**Preventing distribution** -- wrap both sides in a tuple:

```typescript
type ToArrayNonDist<T> = [T] extends [unknown] ? T[] : never;

// Non-distributive: (string | number)[]
type Result2 = ToArrayNonDist<string | number>;
```

### The `infer` keyword

Extract types from within structural positions:

```typescript
// Extract the return type of a function
type MyReturnType<T> = T extends (...args: any[]) => infer R ? R : never;

// Extract array element type
type ElementOf<T> = T extends (infer E)[] ? E : never;

// Extract promise resolved value
type Unpromise<T> = T extends Promise<infer V> ? V : never;

type X = Unpromise<Promise<string>>;  // string
```

### `infer` with constraints (TS 4.7+)

Constrain the inferred type inline:

```typescript
// Only infer if the first element is a string
type FirstIfString<T> =
  T extends [infer S extends string, ...unknown[]] ? S : never;

type Y = FirstIfString<["hello", 1]>;  // "hello"
type Z = FirstIfString<[42, 1]>;       // never
```

### `infer` in template literal types

```typescript
type ExtractRouteParam<T extends string> =
  T extends `${string}:${infer Param}/${infer Rest}`
    ? Param | ExtractRouteParam<Rest>
    : T extends `${string}:${infer Param}`
      ? Param
      : never;

type Params = ExtractRouteParam<"/api/:version/users/:id">;
// "version" | "id"
```

### Recursive conditional types

```typescript
type DeepReadonly<T> = T extends Function
  ? T
  : T extends object
    ? { readonly [K in keyof T]: DeepReadonly<T[K]> }
    : T;
```

---

## 2. Mapped Types

### Basic mapped types

```typescript
type Readonly<T> = { readonly [K in keyof T]: T[K] };
type Optional<T> = { [K in keyof T]?: T[K] };
```

### Modifier removal with `-`

```typescript
type Mutable<T> = { -readonly [K in keyof T]: T[K] };
type Required<T> = { [K in keyof T]-?: T[K] };
```

### Key remapping with `as` (TS 4.1+)

Rename, prefix, or filter keys during iteration:

```typescript
// Prefix all keys with "get"
type Getters<T> = {
  [K in keyof T as `get${Capitalize<string & K>}`]: () => T[K];
};

interface Person { name: string; age: number }
type PersonGetters = Getters<Person>;
// { getName: () => string; getAge: () => number }
```

### Filtering keys with `as` + `never`

Returning `never` from the `as` clause removes the key:

```typescript
// Keep only string-valued properties
type StringProps<T> = {
  [K in keyof T as T[K] extends string ? K : never]: T[K];
};

interface Mixed { name: string; age: number; email: string }
type OnlyStrings = StringProps<Mixed>;
// { name: string; email: string }
```

### Homomorphic mapped types

A mapped type `{ [P in keyof T]: ... }` is **homomorphic** -- it preserves the property modifiers (readonly, optional) of the source type `T`. This is what makes `Readonly<T>` and `Partial<T>` work correctly.

Key fact (a common myth, corrected): the compiler keys homomorphism on the **`in keyof T` constraint**, *not* on the presence of an `as` clause. Adding `as` does **not** by itself break homomorphism -- modifiers are still copied for every key that *survives* the remap. Only keys whose **identity changes** (e.g. remapped to a template-literal string) lose 1:1 modifier provenance, because the output key differs from the source key. So `{ [K in keyof T as F<K>]: ... }` remains modifier-homomorphic over its surviving keys.

```typescript
// Homomorphic: preserves readonly/optional modifiers
type Copy<T> = { [K in keyof T]: T[K] };

// Still homomorphic over surviving keys: `as` does NOT disable modifier copying.
// Only keys whose identity CHANGES (here, renamed to template-literal strings) lose
// their 1:1 modifier mapping, because the output key differs from the source key.
type Renamed<T> = { [K in keyof T as `prefix_${string & K}`]: T[K] };
```

### Intersection via mapped types

```typescript
type Merge<A, B> = {
  [K in keyof A | keyof B]: K extends keyof B
    ? B[K]
    : K extends keyof A
      ? A[K]
      : never;
};
```

---

## 3. Branded / Nominal Types

TypeScript uses structural typing. Branded types simulate nominal typing by adding a phantom property that makes structurally identical types incompatible.

### Pattern 1: Intersection brand

```typescript
type Brand<T, B extends string> = T & { readonly __brand: B };

type UserId = Brand<string, "UserId">;
type OrderId = Brand<string, "OrderId">;

function getUser(id: UserId) { /* ... */ }

const userId = "abc" as UserId;
const orderId = "xyz" as OrderId;

getUser(userId);   // OK
getUser(orderId);  // Error: OrderId not assignable to UserId
getUser("raw");    // Error: string not assignable to UserId
```

### Pattern 2: Unique symbol brand (library-safe)

Unique symbols guarantee the brand key is truly unique, even across modules:

```typescript
declare const UserIdBrand: unique symbol;
declare const OrderIdBrand: unique symbol;

type UserId = string & { readonly [UserIdBrand]: true };
type OrderId = string & { readonly [OrderIdBrand]: true };
```

### Pattern 3: Flavor (weaker brand)

Flavored types accept unbranded values but reject differently-flavored ones:

```typescript
type Flavor<T, F extends string> = T & { readonly __flavor?: F };

type Meters = Flavor<number, "Meters">;
type Seconds = Flavor<number, "Seconds">;

function travel(distance: Meters, time: Seconds) { /* ... */ }

travel(100 as Meters, 10 as Seconds);  // OK
travel(100, 10);                        // OK -- unbranded accepted
travel(100 as Seconds, 10 as Meters);   // Error -- cross-flavor rejected
```

**Brand vs Flavor decision:** Use Brand when all values MUST go through a factory/validator. Use Flavor when you want softer guardrails that still catch cross-domain mistakes.

### Factory functions with runtime validation

```typescript
type Email = Brand<string, "Email">;

function createEmail(input: string): Email {
  if (!/^[^@]+@[^@]+\.[^@]+$/.test(input)) {
    throw new Error(`Invalid email: ${input}`);
  }
  return input as Email;
}

// Type guard for branded types
function isEmail(value: string): value is Email {
  return /^[^@]+@[^@]+\.[^@]+$/.test(value);
}
```

---

## 4. Type Narrowing

### Discriminated unions

```typescript
type Shape =
  | { kind: "circle"; radius: number }
  | { kind: "rect"; width: number; height: number };

function area(s: Shape): number {
  switch (s.kind) {
    case "circle": return Math.PI * s.radius ** 2;   // narrowed
    case "rect":   return s.width * s.height;         // narrowed
  }
}
```

### Exhaustiveness checking

```typescript
function assertNever(x: never): never {
  throw new Error(`Unexpected value: ${x}`);
}

function area(s: Shape): number {
  switch (s.kind) {
    case "circle": return Math.PI * s.radius ** 2;
    case "rect":   return s.width * s.height;
    default:       return assertNever(s);  // compile error if a variant is missed
  }
}
```

### Custom type guards

```typescript
function isString(value: unknown): value is string {
  return typeof value === "string";
}

// Narrowing with type predicate on object properties
function hasName(obj: unknown): obj is { name: string } {
  return typeof obj === "object" && obj !== null && "name" in obj;
}
```

### Assertion functions (TS 3.7+)

Assertion functions narrow the type for all subsequent code in the same scope:

```typescript
function assertDefined<T>(val: T | undefined | null, msg?: string): asserts val is T {
  if (val == null) throw new Error(msg ?? "Expected defined value");
}

function process(input: string | undefined) {
  assertDefined(input);
  // input is now `string` for the rest of the function
  console.log(input.toUpperCase());
}
```

### The `satisfies` operator (TS 4.9+)

`satisfies` validates a value against a type WITHOUT widening the inferred type:

```typescript
type ColorMap = Record<string, [number, number, number] | string>;

// With `: ColorMap` annotation -- widens, loses literal info
const colorsAnnotated: ColorMap = {
  red: [255, 0, 0],
  green: "#00ff00",
};
colorsAnnotated.red.map(x => x);  // Error: string | number[] has no .map

// With `satisfies` -- validates but keeps narrow inference
const colors = {
  red: [255, 0, 0],
  green: "#00ff00",
} satisfies ColorMap;

colors.red.map(x => x);      // OK: inferred as [number, number, number]
colors.green.toUpperCase();   // OK: inferred as string
```

**When to use `satisfies`:**
- Config objects where you want validation + precise autocomplete
- Discriminated union values where the discriminant literal must be preserved
- `as const` objects that must conform to a schema

### `in` operator narrowing

```typescript
type Fish = { swim: () => void };
type Bird = { fly: () => void };

function move(animal: Fish | Bird) {
  if ("swim" in animal) {
    animal.swim();  // narrowed to Fish
  } else {
    animal.fly();   // narrowed to Bird
  }
}
```

---

## 5. Generic Constraints

### Basic constraints with `extends`

```typescript
function getLength<T extends { length: number }>(item: T): number {
  return item.length;
}

getLength("hello");     // OK
getLength([1, 2, 3]);   // OK
getLength(42);           // Error: number has no 'length'
```

### `const` type parameters (TS 5.0+)

Infer literal types by default instead of widened types:

```typescript
// Without const: routes inferred as string[]
declare function defineRoutes<T extends readonly string[]>(routes: T): T;
const r1 = defineRoutes(["/home", "/about"]);  // string[]

// With const: routes inferred as readonly ["/home", "/about"]
declare function defineRoutes<const T extends readonly string[]>(routes: T): T;
const r2 = defineRoutes(["/home", "/about"]);  // readonly ["/home", "/about"]
```

### Constrained generics with defaults

```typescript
type EventMap = {
  click: { x: number; y: number };
  keydown: { key: string };
};

function on<K extends keyof EventMap = keyof EventMap>(
  event: K,
  handler: (payload: EventMap[K]) => void
): void { /* ... */ }
```

### The `extends` constraint in conditional types vs generics

```typescript
// Generic constraint: T MUST extend string
function process<T extends string>(val: T): T { return val; }

// Conditional type: checks if T extends string (not a constraint, a condition)
type Check<T> = T extends string ? "yes" : "no";
```

---

## 6. Variadic Tuple Types (TS 4.0+)

### Spread in tuple types

```typescript
type Concat<A extends readonly unknown[], B extends readonly unknown[]> =
  [...A, ...B];

type AB = Concat<[1, 2], [3, 4]>;  // [1, 2, 3, 4]
```

### Inferring tuple segments

```typescript
type Head<T extends readonly unknown[]> =
  T extends [infer H, ...unknown[]] ? H : never;

type Tail<T extends readonly unknown[]> =
  T extends [unknown, ...infer Rest] ? Rest : never;

type Last<T extends readonly unknown[]> =
  T extends [...unknown[], infer L] ? L : never;

type H = Head<[1, 2, 3]>;  // 1
type T = Tail<[1, 2, 3]>;  // [2, 3]
type L = Last<[1, 2, 3]>;  // 3
```

### Typed function composition

```typescript
type PipeArgs<Fns extends readonly Function[]> =
  Fns extends [(...args: infer A) => infer R, ...infer Rest extends Function[]]
    ? Rest extends [((arg: R) => any), ...any[]]
      ? [(...args: A) => R, ...PipeArgs<Rest>]
      : [(...args: A) => R]
    : [];
```

### Generic rest elements in tuples

```typescript
// Flexible tuple: starts with string, ends with number, anything in between
type Bookend<T extends readonly unknown[]> = [string, ...T, number];

type Example = Bookend<[boolean, Date]>;  // [string, boolean, Date, number]
```

### Constraint pattern: `readonly unknown[] | []`

The `[]` in the union forces tuple inference for array literals instead of widening to arrays:

```typescript
declare function tuple<T extends readonly unknown[] | []>(values: T): T;

const result = tuple([1, "a", true]);  // readonly [1, "a", true]
```

---

## 7. Template Literal Types

### Basic template literal types

```typescript
type EventName = `on${Capitalize<"click" | "focus" | "blur">}`;
// "onClick" | "onFocus" | "onBlur"
```

### Built-in string manipulation types

```typescript
type U = Uppercase<"hello">;      // "HELLO"
type L = Lowercase<"HELLO">;      // "hello"
type C = Capitalize<"hello">;     // "Hello"
type N = Uncapitalize<"Hello">;   // "hello"

// They distribute over unions
type Events = Capitalize<"click" | "focus">;  // "Click" | "Focus"
```

### String parsing at the type level

```typescript
type Split<S extends string, D extends string> =
  S extends `${infer Head}${D}${infer Tail}`
    ? [Head, ...Split<Tail, D>]
    : [S];

type Parts = Split<"a.b.c", ".">;  // ["a", "b", "c"]
```

### Type-safe dot-notation paths

```typescript
type PathKeys<T, Prefix extends string = ""> = T extends object
  ? {
      [K in keyof T & string]: T[K] extends object
        ? PathKeys<T[K], `${Prefix}${K}.`> | `${Prefix}${K}`
        : `${Prefix}${K}`;
    }[keyof T & string]
  : never;

interface Config {
  db: { host: string; port: number };
  app: { name: string };
}

type ConfigPaths = PathKeys<Config>;
// "db" | "db.host" | "db.port" | "app" | "app.name"
```

### Template literal + mapped types (type-safe event emitters)

```typescript
type Emitter<Events extends Record<string, unknown>> = {
  on<K extends string & keyof Events>(
    event: K,
    handler: (payload: Events[K]) => void,
  ): void;
  emit<K extends string & keyof Events>(
    event: K,
    payload: Events[K],
  ): void;
};
```

### Performance warning

Template literal types create combinatorial unions. Interpolating two unions of size M and N produces M x N members. Keep interpolated unions under ~10 members each to avoid compiler slowdowns.

```typescript
// DANGEROUS: 26 * 26 * 26 = 17,576 union members
type Alpha = "a" | "b" | /* ... */ "z";
type ThreeLetterCodes = `${Alpha}${Alpha}${Alpha}`;  // compiler will struggle
```

---

## 8. Utility Types -- Deep Dive

### `NoInfer<T>` (TS 5.4+)

Blocks TypeScript from using a position for type inference:

```typescript
// Without NoInfer: T inferred from BOTH value and defaultValue
function getOrDefault<T>(value: T | undefined, defaultValue: T): T {
  return value ?? defaultValue;
}
getOrDefault("hello", 42);  // No error -- T widened to string | number

// With NoInfer: T inferred from value only, defaultValue just checked
function getOrDefault<T>(value: T | undefined, defaultValue: NoInfer<T>): T {
  return value ?? defaultValue;
}
getOrDefault("hello", 42);  // Error: number not assignable to string
```

**Use cases for `NoInfer`:**
- Preventing default parameters from influencing generic inference
- Ensuring one argument "drives" the generic while others are checked against it
- API design where inference direction matters

### `Awaited<T>` (TS 4.5+)

Recursively unwraps `Promise` types:

```typescript
type A = Awaited<Promise<string>>;                  // string
type B = Awaited<Promise<Promise<number>>>;          // number
type C = Awaited<string | Promise<boolean>>;         // string | boolean
```

### `Parameters<T>` and `ConstructorParameters<T>`

```typescript
function greet(name: string, age: number): string { return ""; }

type GreetParams = Parameters<typeof greet>;  // [name: string, age: number]

// Re-use parameter types in wrapper functions
function loggedGreet(...args: Parameters<typeof greet>): string {
  console.log("Calling greet with", args);
  return greet(...args);
}
```

### `ReturnType<T>` + `Awaited` pattern

```typescript
async function fetchUsers() {
  return [{ id: 1, name: "Alice" }];
}

// Derive the resolved return type without importing/duplicating
type Users = Awaited<ReturnType<typeof fetchUsers>>;
// { id: number; name: string }[]
```

### `Omit` + `Pick` for reshaping

```typescript
// Make specific properties optional while keeping the rest required
type PartialBy<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

// Make specific properties required while keeping the rest as-is
type RequiredBy<T, K extends keyof T> = Omit<T, K> & Required<Pick<T, K>>;
```

---

## 9. Type-Level Performance

### Avoid deep instantiation

Deeply nested generics are the primary cause of slow type checking. The compiler has hard limits:
- **Type instantiation depth:** 50 levels (error: "Type instantiation is excessively deep and possibly infinite")
- **Type instantiation count:** 5,000,000 total instantiations
- **Union constituent limit:** 100,000 members

### Tail-call optimization for recursive types

TypeScript recognizes tail-position recursive type aliases and can handle deeper recursion:

```typescript
// NON-TAIL -- accumulator is wrapped, hits depth limit quickly
type Reverse_Bad<T extends unknown[], Acc extends unknown[] = []> =
  T extends [infer H, ...infer Rest]
    ? Reverse_Bad<Rest, [H, ...Acc]>  // recursive call is in tail position here
    : Acc;

// TAIL -- the recursive call IS the result (good pattern)
type TupleToUnion<T extends readonly unknown[]> =
  T extends [infer H, ...infer Rest]
    ? H | TupleToUnion<Rest>     // each branch resolves directly
    : never;
```

### Reducing type complexity

```typescript
// BAD: creates deep instantiation chain
type DeepPartial<T> = {
  [K in keyof T]?: T[K] extends object ? DeepPartial<T[K]> : T[K];
};

// BETTER: add a depth limiter
type DeepPartial<T, Depth extends unknown[] = []> =
  Depth["length"] extends 5
    ? T  // bail out at depth 5
    : {
        [K in keyof T]?: T[K] extends object
          ? DeepPartial<T[K], [...Depth, unknown]>
          : T[K];
      };
```

### Practical performance guidelines

1. **Flatten unions early.** Large intermediate unions compound in later type operations.
2. **Avoid `Extract`/`Exclude` on large unions** in hot paths -- each distributes over every member.
3. **Prefer `interface` over `type` for object shapes.** Interfaces are cached by name; type aliases are structurally re-evaluated.
4. **Use `skipLibCheck: true`** to avoid type-checking `node_modules` .d.ts files in development.
5. **Profile with `--generateTrace`.** Run `tsc --generateTrace traceDir` and open the trace in `chrome://tracing` to find expensive types.
6. **Keep template literal interpolations small.** Two 10-member unions produce 100 variants; three produce 1,000.
7. **Use `interface extends` over intersection `&`** for combining object types -- intersections create anonymous types that are harder for the compiler to cache.

---

## 10. Patterns and Recipes

### Builder pattern with chained generics

```typescript
class QueryBuilder<Selected extends string = never> {
  select<F extends string>(field: F): QueryBuilder<Selected | F> {
    return this as any;
  }
  where(field: Selected, value: unknown): this {
    return this;
  }
}

new QueryBuilder()
  .select("name")
  .select("age")
  .where("name", "Alice")   // OK
  .where("email", "x");     // Error: "email" not in "name" | "age"
```

### Type-safe state machines

```typescript
type Transitions = {
  idle: "loading";
  loading: "success" | "error";
  success: "idle";
  error: "idle" | "loading";
};

type Machine<State extends keyof Transitions> = {
  state: State;
  transition<Next extends Transitions[State]>(
    to: Next
  ): Machine<Next & keyof Transitions>;
};
```

### Extracting union discriminants

```typescript
type DiscriminantValues<T, K extends keyof T> = T extends unknown ? T[K] : never;

type Actions =
  | { type: "ADD"; payload: string }
  | { type: "REMOVE"; id: number };

type ActionTypes = DiscriminantValues<Actions, "type">;  // "ADD" | "REMOVE"
```

### `Exact<T>` -- prevent excess properties in generics

```typescript
type Exact<T, Shape> = T extends Shape
  ? Exclude<keyof T, keyof Shape> extends never
    ? T
    : never
  : never;

function createConfig<T>(config: Exact<T, { host: string; port: number }>): void {}
```

---

## Quick Reference: When to Reach for Each Tool

| Need | Tool |
|---|---|
| Transform every key/value of an object type | Mapped type |
| Conditionally choose a type based on structure | Conditional type |
| Extract a type from inside another type | `infer` |
| Make structurally identical types incompatible | Branded type |
| Validate a value matches a type without widening | `satisfies` |
| Narrow a type in control flow | Type guard / assertion function |
| Infer literal values from generic arguments | `const` type parameter |
| Manipulate string types at the type level | Template literal type |
| Compose tuple types generically | Variadic tuple |
| Control which argument drives generic inference | `NoInfer` |
| Derive types from function signatures | `Parameters` / `ReturnType` |
| Unwrap nested Promises | `Awaited` |

---

## Sources

- [TypeScript Handbook: Conditional Types](https://www.typescriptlang.org/docs/handbook/2/conditional-types.html)
- [TypeScript Handbook: Mapped Types](https://www.typescriptlang.org/docs/handbook/2/mapped-types.html)
- [TypeScript Handbook: Template Literal Types](https://www.typescriptlang.org/docs/handbook/2/template-literal-types.html)
- [TypeScript Handbook: Narrowing](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)
- [TypeScript Handbook: Utility Types](https://www.typescriptlang.org/docs/handbook/utility-types.html)
- [NoInfer: TypeScript 5.4's New Utility Type -- Total TypeScript](https://www.totaltypescript.com/noinfer)
- [Branded Types in TypeScript -- shramko.dev](https://shramko.dev/snippets/branded-types)
- [What the heck is a homomorphic mapped type? -- Andrea Simone Costa](https://andreasimonecosta.dev/posts/what-the-heck-is-a-homomorphic-mapped-type/)
- [Template literal types in TypeScript -- 2ality](https://2ality.com/2025/01/template-literal-types.html)
- [Computing with tuple types in TypeScript -- 2ality](https://2ality.com/2025/01/typescript-tuples.html)
- [Conditional types in TypeScript -- 2ality](https://2ality.com/2025/02/conditional-types-typescript.html)
- [TypeScript Performance Optimization 2026 -- DEV Community](https://dev.to/_d7eb1c1703182e3ce1782/typescript-performance-optimization-2026-compile-speed-runtime-efficiency-and-type-safety-48ch)
