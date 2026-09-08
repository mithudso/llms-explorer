---
title: "TypeScript Compiler API"
description: "A lang-js-ts reference for driving the typescript npm package as a library — parsing source to"
---

# TypeScript Compiler API & Programmatic Tooling (Strada)

A `lang-js-ts` reference for driving the **`typescript` npm package as a library** — parsing source to
an AST, type-checking through the `TypeChecker`, rewriting code with **custom transformers** built on
the modern `ts.factory` node API, hosting the **Language Service**, and the **ts-morph** wrapper that
makes all of it ergonomic. This is the engine behind linters, codemods, code generators, doc tools,
and editor plugins. For the type *system* and `tsconfig` defer to `typescript-expert.md` /
`typescript-compiler-config`; for *running* `.ts` (type stripping, tsx, ts-node) defer to
`nodejs-typescript-and-runtime-features.md`.

## Overview

The compiler ships one public module (`import * as ts from "typescript"`) exposing the same pipeline
`tsc` uses: a **scanner/parser** turns text into an immutable **AST** (`ts.SourceFile` of `ts.Node`s);
a **binder** + **`TypeChecker`** resolve symbols and types; **transformers** rewrite the tree; a
**printer/emitter** writes `.js`/`.d.ts`. You opt into as much of that as you need — a one-file
syntactic codemod uses only the parser; a type-aware lint rule needs a full `Program` + checker.

**The single most important framing fact — Strada vs Corsa:** everything in this skill is the
**"Strada"** API, the original JavaScript/TypeScript-based compiler. **TS 6.0 (2026-03-23) is the
final JS-based release.** **TS 7.0 "Corsa"** is a ground-up Go port (≈10× faster) that **does *not*
support the Strada compiler API** — a replacement programmatic API is in progress and not stable as
of mid-2026. So any tool you write against this surface targets **TS ≤ 6.x**. `ts-morph` wraps Strada
too, so it shares that ceiling. Plan migrations accordingly; don't assume your transformer/LS plugin
carries to 7.x.

**Version anchors (memorize — these drive most "does this API exist" questions):**

| Fact | Version | Notes |
| --- | --- | --- |
| `ts.factory.createXxx` node API introduced | TS **4.0** | the supported way to build/update nodes |
| Bare `ts.createXxx` factory fns deprecated | 4.0–4.9 | aliases still callable (verified present in 4.9.5) |
| Bare `ts.createXxx` / `ts.createNode` / `updateXxx` **removed** | TS **5.0** | verified `undefined` in 5.8.3 **and** 6.0.3 — use `ts.factory.*` |
| Compiler API surface (`createProgram`, checker, transformers, LS) | unchanged across **5.x–6.x** | every snippet here runs on both |
| Last **JS-based** TS release (this API) | **6.0** (6.0.3 current) | shipped 2026-03-23 |
| TS **7.0 "Corsa"** (Go port) | in progress | **drops the Strada API**; no stable replacement API yet |
| `ts.createSourceFile` (parser entry) | always present | NOT a factory node-creator — see Core Concept 1 |

> Caveat: `ts.createSourceFile` survives because it is the **parser** entry point (text → tree), a
> different thing from the removed *factory* `ts.createXxx` node builders. Don't be misled by the name
> overlap.

## Core Concepts

### 1. Two entry points: `createSourceFile` (parse only) vs `createProgram` (has a checker)

- **`ts.createSourceFile(fileName, text, langVersion, setParentNodes?)`** parses ONE in-memory string
  into a `SourceFile`. No types, no cross-file resolution, no checker. This is all a *syntactic*
  codemod/linter needs. Pass `setParentNodes = true` if you'll call `node.getStart()`/`getText()`
  (they need parent pointers — see Concept 5).
- **`ts.createProgram(rootFileNames, options, host?)`** builds a multi-file **`Program`**: it resolves
  imports, runs the binder, and is the **only** way to get a `TypeChecker` via
  `program.getTypeChecker()`. Use it for anything *type-aware*. `options` is a `CompilerOptions`
  (defer the option semantics to `typescript-compiler-config`).

```ts
import * as ts from "typescript";

// Parse-only (syntactic):
const sf = ts.createSourceFile("x.ts", "const a: number = 1;", ts.ScriptTarget.Latest, /*parents*/ true);

// Type-aware:
const program = ts.createProgram(["src/index.ts"], {
  target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.NodeNext, strict: true,
});
const checker = program.getTypeChecker();
```

### 2. The CompilerHost — controlling I/O

`createProgram`'s third arg is a `CompilerHost`: the abstraction the compiler uses to read files,
resolve modules, and write output. `ts.createCompilerHost(options)` gives the default disk-backed
host; **override its methods** to feed source from memory, a VFS, or a network, and to capture emit
output instead of writing to disk.

```ts
const options: ts.CompilerOptions = { target: ts.ScriptTarget.ES2022 };
const host = ts.createCompilerHost(options);
const realRead = host.readFile.bind(host);
host.readFile = (f) => (f === "/virtual/a.ts" ? "export const a = 1;" : realRead(f));
const program = ts.createProgram(["/virtual/a.ts"], options, host);
```

### 3. Diagnostics

- **`ts.getPreEmitDiagnostics(program)`** → all syntactic + semantic + global errors *before* emit.
- **`program.emit()`** returns an `EmitResult` whose `.diagnostics` are emit-time errors; combine via
  `ts.getPreEmitDiagnostics(program).concat(emitResult.diagnostics)`.
- Format for humans: **`ts.formatDiagnosticsWithColorAndContext(diags, host)`** (ANSI, code frames) or
  `ts.formatDiagnostics(diags, host)` (plain). For a single message string use
  `ts.flattenDiagnosticMessageText(d.messageText, "\n")`.

```ts
const diagnostics = ts.getPreEmitDiagnostics(program);
if (diagnostics.length) {
  const fmtHost: ts.FormatDiagnosticsHost = {
    getCanonicalFileName: (p) => p,
    getCurrentDirectory: ts.sys.getCurrentDirectory,
    getNewLine: () => ts.sys.newLine,
  };
  process.stderr.write(ts.formatDiagnosticsWithColorAndContext(diagnostics, fmtHost));
}
```

### 4. Emitting JS

`program.emit(targetSourceFile?, writeFile?, cancellationToken?, emitOnlyDtsFiles?, customTransformers?)`
writes output through the host (or your `writeFile` callback). The 5th arg accepts
`{ before, after, afterDeclarations }` transformer arrays — this is how you run a transformer
*through* the compiler (vs the standalone `ts.transform`, Concept 6). `emitOnlyDtsFiles: true` emits
declarations only — but **declaration-emit semantics and hand-authoring `.d.ts` are out of scope** →
`typescript-declaration-files`.

### 5. The AST: nodes, kinds, walking, positions, trivia

- A `ts.Node` has a numeric **`kind`** (`ts.SyntaxKind` enum). Narrow with **type guards**:
  `ts.isFunctionDeclaration(node)`, `ts.isCallExpression(node)`, `ts.isIdentifier(node)`, etc. — these
  give correct TS narrowing, far better than raw `kind ===` checks.
- **Walking — two different traversals, a classic codemod trap:**
  - **`ts.forEachChild(node, cb)`** visits only the **semantically significant** child nodes; it
    **skips tokens, punctuation, and trivia**. Use it for analysis/codemods. Returning a truthy value
    short-circuits (like `Array.find`).
  - **`node.getChildren(sourceFile?)`** returns **every** child *including* token nodes (braces,
    commas, keywords). Heavier; needed when you care about punctuation. **Requires a parsed tree with
    parent pointers** — throws on synthesized factory nodes.
- **Positions / text / trivia:** `node.getStart(sf)` (start *after* leading trivia), `node.pos` (raw
  start, *includes* leading trivia), `node.end`, `node.getText(sf)`, `node.getFullText(sf)` (with
  trivia), `ts.getLeadingCommentRanges(fullText, node.pos)` for comments. **All of these need a real
  parsed `SourceFile` with `setParentNodes`/parents** — on `ts.factory`-created nodes `pos`/`end` are
  `-1` and these throw.

```ts
function findLongFunctions(sf: ts.SourceFile, maxLines = 50): string[] {
  const offenders: string[] = [];
  const visit = (node: ts.Node): void => {
    if (ts.isFunctionDeclaration(node) && node.body) {
      const start = sf.getLineAndCharacterOfPosition(node.getStart(sf)).line;
      const end = sf.getLineAndCharacterOfPosition(node.end).line;
      if (end - start > maxLines) offenders.push(node.name?.text ?? "<anon>");
    }
    ts.forEachChild(node, visit); // recurse
  };
  visit(sf);
  return offenders;
}
```

### 6. The TypeChecker — resolving types and symbols

The checker is where *meaning* lives. You **must** have a `Program` (a parse-only `SourceFile` has no
checker). Core methods:

- **`checker.getTypeAtLocation(node)`** → the `Type` at any expression/decl node.
- **`checker.getSymbolAtLocation(node)`** → the `Symbol` (declaration identity) for a name node.
- **`checker.getTypeOfSymbolAtLocation(symbol, node)`** → a symbol's type *in context* (handles
  overloads/locations).
- **`checker.typeToString(type)`** → human-readable type text (e.g. `(name: string) => string`).
- Signatures: `type.getCallSignatures()` → `Signature[]`; `sig.getReturnType()`,
  `sig.getParameters()`. Symbols: `symbol.getName()`, `symbol.valueDeclaration`,
  `checker.getDeclaredTypeOfSymbol(sym)`, `checker.getPropertiesOfType(type)`.

```ts
// VERIFIED against ts 6.0.3 — extract every exported function's signature.
function dumpSignatures(program: ts.Program, fileName: string): void {
  const checker = program.getTypeChecker();
  const sf = program.getSourceFile(fileName)!;
  ts.forEachChild(sf, (node) => {
    if (ts.isFunctionDeclaration(node) && node.name) {
      const sym = checker.getSymbolAtLocation(node.name);
      if (!sym?.valueDeclaration) return;
      const type = checker.getTypeOfSymbolAtLocation(sym, sym.valueDeclaration);
      console.log(node.name.text, "::", checker.typeToString(type));
      for (const sig of type.getCallSignatures()) {
        console.log("  returns:", checker.typeToString(sig.getReturnType()));
      }
    }
  });
}
// greet :: (name: string) => string  /  returns: string
```

### 7. Custom transformers with `ts.factory`

A **`TransformerFactory<T>`** is `(context: ts.TransformationContext) => (node: T) => T`. Inside, you
recurse with **`ts.visitEachChild(node, visitor, context)`** (rewrites children) and return
**replacement nodes built with `ts.factory.createXxx`** — the AST is immutable, so you *create new*
nodes or **update** existing ones (`ts.factory.updateXxx(original, ...newChildren)` preserves position
and emit info — prefer it over `create` when editing in place).

Run a transformer two ways:
1. **Standalone:** `ts.transform(sourceOrNodes, [transformer], options?)` → `TransformationResult`;
   print with `ts.createPrinter().printNode(...)` or `printFile(...)`. Call `result.dispose()`.
2. **Through emit:** pass `{ before: [t] }` as the 5th arg to `program.emit(...)`.

`before` runs before TS's built-in transforms, `after` runs after them (on downleveled output),
`afterDeclarations` transforms the `.d.ts` tree.

```ts
// VERIFIED against ts 6.0.3 — rewrite the string literal "foo" → "bar".
const replaceFoo: ts.TransformerFactory<ts.SourceFile> = (context) => {
  const visit: ts.Visitor = (node) => {
    if (ts.isStringLiteral(node) && node.text === "foo") {
      return ts.factory.createStringLiteral("bar");      // NEW node (not ts.createStringLiteral — removed in 5.0)
    }
    return ts.visitEachChild(node, visit, context);       // recurse into children
  };
  return (sf) => ts.visitNode(sf, visit) as ts.SourceFile;
};

const sf = ts.createSourceFile("t.ts", 'const a = "foo"; console.log(a);', ts.ScriptTarget.Latest, true);
const result = ts.transform(sf, [replaceFoo]);
const printed = ts.createPrinter().printNode(ts.EmitHint.Unspecified, result.transformed[0], sf);
result.dispose();
// printed === 'const a = "bar";\nconsole.log(a);'
```

> `ts.visitNode` visits a single node; `ts.visitEachChild` visits its children — you typically pair
> them (top-level `visitNode`, recursive `visitEachChild`). To synthesize entirely new code, compose
> `ts.factory` calls (e.g. `ts.factory.createCallExpression(ts.factory.createIdentifier("log"), undefined, [arg])`).

### 8. Plugging transformers into a build — the `tsc` gap

**Vanilla `tsc` (the CLI) runs NO custom transformers.** There is no tsconfig flag for it. Your
options, from most to least direct:

- **Programmatically** — `ts.transform` or `program.emit(…, { before, after })` (Concept 7). Full
  control; you own the build script.
- **Build-tool integration** — most loaders accept transformers: `ts-loader`
  (`options.getCustomTransformers`), `ts-jest`, `rollup-plugin-typescript2`, etc. Bundlers using
  esbuild/swc do *not* run TS transformers (different engine) → `nodejs-build-tooling-bundlers`.
- **Patch `tsc`** — **`ts-patch`** (the maintained successor to the older **`ttypescript`**) adds a
  **`plugins`** array under **`compilerOptions`** so `tspc` (its patched CLI) runs transformers during
  a normal build. Keys: **`transform`** (module path, required), **`after`**, **`afterDeclarations`**,
  **`transformProgram`**, **`import`** (named export), **`type`**. (Its persistent in-`node_modules`
  patch mode is "more limited in TypeScript 6+"; prefer the live `tspc`/`ts-patch/compiler` path.)

```jsonc
// tsconfig.json — ts-patch / ttypescript build transformers (NOT vanilla tsc, NOT LS plugins)
{ "compilerOptions": { "plugins": [ { "transform": "./my-transformer.ts", "after": true } ] } }
```

> **Do not confuse this with the native `compilerOptions.plugins` array — that one is Language Service
> plugins only (Concept 9). Same JSON key, completely different mechanism.**

### 9. The Language Service + tsserver LS plugins

The **Language Service** (`ts.createLanguageService(host, registry?)`) is the *incremental, editor*
half of the compiler: it answers completions, quick-info (hover), diagnostics, go-to-definition,
rename, and refactors. You feed it a **`LanguageServiceHost`** — like a `CompilerHost` but built for
mutation: it must report file *versions* (bump the version string when a file changes) so the service
re-checks only what moved.

```ts
const files: Record<string, { text: string; version: number }> = {
  "main.ts": { text: "const n: number = 1; n.toFixe", version: 0 },
};
const servicesHost: ts.LanguageServiceHost = {
  getScriptFileNames: () => Object.keys(files),
  getScriptVersion: (f) => String(files[f]?.version ?? 0),
  getScriptSnapshot: (f) =>
    files[f] ? ts.ScriptSnapshot.fromString(files[f].text) : undefined,
  getCurrentDirectory: () => process.cwd(),
  getCompilationSettings: () => ({ target: ts.ScriptTarget.ES2022 }),
  getDefaultLibFileName: (o) => ts.getDefaultLibFilePath(o),
  readFile: ts.sys.readFile,
  fileExists: ts.sys.fileExists,
};
const service = ts.createLanguageService(servicesHost, ts.createDocumentRegistry());
const completions = service.getCompletionsAtPosition("main.ts", 29, {});
const semantic = service.getSemanticDiagnostics("main.ts");
```

**tsserver Language-Service plugins** wrap this service to add editor features for everyone using the
project (e.g. a framework's template-aware completions). You ship a module exporting
`function init({ typescript }) { return { create(info) { /* wrap info.languageService */ return proxy; } }; }`
and register it in tsconfig's **native** `compilerOptions.plugins`:

```jsonc
{ "compilerOptions": { "plugins": [ { "name": "my-ts-plugin" } ] } } // editor only; tsc ignores it
```

These run **inside the editor's tsserver**, not in `tsc` builds — they change the dev experience, not
the emitted output.

### 10. ts-morph — the high-level wrapper

`ts-morph` wraps the compiler API with a navigable, mutable object model so you skip the visitor/factory
boilerplate. Use it for **navigation, refactoring, and codegen ergonomics**; drop to the raw API only
when you need something it doesn't expose (then reach `node.compilerNode` for the underlying `ts.Node`,
and `project.getTypeChecker().compilerObject` for the raw checker).

- **`new Project({ tsConfigFilePath })`** (or `useInMemoryFileSystem: true`) is the root.
- Load: `project.addSourceFilesAtPaths("src/**/*.ts")`, `addSourceFileAtPath(p)`,
  `createSourceFile(path, text)`.
- Navigate: `sourceFile.getFunctionOrThrow("name")`, `getClasses()`,
  `getDescendantsOfKind(SyntaxKind.CallExpression)`, `node.getType().getText()`.
- Manipulate: `fn.rename("sum")` (project-wide rename!), `cls.addMethod({...})`,
  `node.replaceWithText(...)`, `sourceFile.addImportDeclaration({...})`.
- Persist: `await project.save()` writes changed files back.

```ts
// VERIFIED against ts-morph 28 (bundles ts 6.0.2).
import { Project, SyntaxKind } from "ts-morph";
const project = new Project({ useInMemoryFileSystem: true });
const sf = project.createSourceFile("a.ts", "export function add(a: number, b: number) { return a + b; }");
const fn = sf.getFunctionOrThrow("add");
fn.getReturnType().getText();      // "number"  (full checker behind it)
fn.rename("sum");                  // updates every reference in the project
sf.getFullText();                  // "export function sum(a: number, b: number) { return a + b; }"
```

**Raw API vs ts-morph:** raw is leaner (no extra dep), exact, and what you need for build-time
transformers and LS plugins; ts-morph is faster to write for one-shot codemods, scaffolding/codegen,
and bulk renames. Both target Strada (TS ≤ 6.x).

### 11. typescript-eslint `parserServices` (pointer only)

For **type-aware lint rules**, `@typescript-eslint/parser` (with `parserOptions.project`) attaches
**`parserServices`** to each rule, exposing `getTypeChecker()` and
`esTreeNodeToTSNodeMap`/`tsNodeToESTreeNodeMap` to bridge the ESLint ESTree node to the TS `Node` and
its `Type`. That is the entry point for the whole typed-lint domain — **authoring those rules is out
of scope** → `typescript-eslint-typed-linting`.

## Tools / Frameworks

- **`typescript` (the package)** — `ts.createProgram`, `ts.createSourceFile`, `ts.createCompilerHost`,
  `program.getTypeChecker()`, `program.emit()`, `ts.transform`, `ts.createPrinter`, `ts.factory.*`,
  `ts.createLanguageService`. Strada API; TS ≤ 6.x.
- **ts-morph** — high-level wrapper (`Project`, `SourceFile`, `getDescendantsOfKind`, `rename`,
  `save`); bundles its own TS (6.0.2 in v28).
- **ts-patch** (`tspc`) — successor to **ttypescript**; runs build transformers via
  `compilerOptions.plugins`.
- **`@typescript-eslint/parser` `parserServices`** — bridge to the checker for typed lint rules
  (defer rule authoring).

## Methodology

1. **Pick the entry point by need.** Syntactic-only (formatting, simple codemod) → `createSourceFile`
   (set `setParentNodes` if you read positions). Anything type-aware → `createProgram` + checker.
2. **Choose raw vs ts-morph.** One-shot codemod / scaffolding / bulk rename → ts-morph. Build-time
   transformer or LS plugin → raw API (no wrapper in the build path).
3. **Walk with the right traversal.** Analysis → `forEachChild` + `ts.isXxx` guards. Need tokens/punct
   → `getChildren` (parsed tree only).
4. **Mutate immutably.** Build with `ts.factory.createXxx`; prefer `ts.factory.updateXxx` when editing
   in place; recurse with `visitEachChild`; print with `createPrinter`.
5. **Decide how it runs.** Programmatic (`ts.transform` / `emit`), build-tool loader, or `ts-patch`.
   Never expect vanilla `tsc` to run it.
6. **Read diagnostics** via `getPreEmitDiagnostics` (+ emit diagnostics); format with
   `formatDiagnosticsWithColorAndContext`.
7. **Mind the ceiling.** This is Strada (TS ≤ 6.x); TS 7 "Corsa" won't run it — note that in any tool's
   compatibility docs.

## Practical Patterns

- **AST linter:** parse-only `createSourceFile` → `forEachChild` + guards → collect
  `{ file, line, message }` from `getLineAndCharacterOfPosition(node.getStart(sf))`.
- **Type extractor / API surface:** `createProgram` → checker → for each exported symbol
  `getTypeOfSymbolAtLocation` + `typeToString` (and `getCallSignatures`) → dump JSON.
- **Codemod:** `TransformerFactory` with `ts.factory.updateXxx` → `ts.transform` → `printer.printFile`
  → write back; or ts-morph `getDescendantsOfKind` + `replaceWithText` + `project.save()`.
- **Codegen:** assemble brand-new files from `ts.factory` nodes, or `project.createSourceFile(path,
  templateText)` then refine via the model.
- **Build-plugged transform:** author once, register under `ts-patch` `compilerOptions.plugins`
  (`transform`/`after`), build with `tspc`.
- **Editor feature:** `LanguageServiceHost` with versioned snapshots → `createLanguageService` →
  `getCompletionsAtPosition` / `getSemanticDiagnostics`; ship as a tsserver plugin via native
  `compilerOptions.plugins`.

## Anti-Patterns

- Calling `ts.createIdentifier` / `ts.createCall` / `ts.createNode` / `ts.updateXxx` — **removed in
  TS 5.0** (verified `undefined` in 5.8.3 and 6.0.3). Always `ts.factory.createXxx` / `updateXxx`.
- Mutating `node` fields in place — the AST is immutable; create or `update` nodes instead.
- Reading `getStart`/`getText`/`getChildren`/positions on `ts.factory`-synthesized nodes (pos/end =
  -1) — they throw; those need a parsed tree with parent pointers (`setParentNodes`).
- Confusing `forEachChild` (named children, no tokens) with `getChildren()` (all tokens) — picking the
  wrong one silently skips or floods nodes in a codemod.
- Expecting **vanilla `tsc`** to run a transformer — it never does; use programmatic emit, a loader, or
  `ts-patch`.
- Conflating the **two `plugins` arrays**: native `compilerOptions.plugins` = LS/editor plugins (`tsc`
  ignores); `ts-patch`'s `compilerOptions.plugins` (with `transform`) = build transformers.
- Asking `getTypeChecker()` on a parse-only `SourceFile` — there's no checker without a `Program`.
- Assuming compiler-API tooling (or ts-morph) survives the move to **TS 7 "Corsa"** — Strada API is
  dropped; budget a rewrite.

## Troubleshooting

- `ts.createXxx is not a function` → removed in 5.0; switch to `ts.factory.createXxx`.
- `Cannot read properties of undefined (reading 'getStart'/'pos')` or `-1` positions → node is
  synthesized (factory) or you parsed without `setParentNodes`; re-parse with parents or don't read
  positions off synthetic nodes.
- Checker returns `any`/`undefined` symbols → the file isn't in the `Program`'s root set, or imports
  didn't resolve (check `CompilerOptions.module`/`moduleResolution`, or a custom host's `readFile`).
- Transformer "did nothing" under `tsc` → vanilla `tsc` ignores transformers; run via `ts.transform`,
  `program.emit({before})`, a loader, or `tspc`.
- LS plugin not loading → it only runs in the editor's tsserver, not `tsc`; confirm the editor uses the
  workspace TS version and the plugin name resolves.
- `getCompletionsAtPosition` stale after edits → bump the file's `getScriptVersion` string so the
  Language Service invalidates its cache.

## References

- TS wiki — Using the Compiler API: https://github.com/microsoft/TypeScript/wiki/Using-the-Compiler-API
- `typescript` package source / API (probed at runtime, 6.0.3 / 5.8.3 / 4.9.5): https://github.com/microsoft/TypeScript
- ts-morph docs (bundles ts 6.0.2): https://ts-morph.com/
- ts-patch (successor to ttypescript; `compilerOptions.plugins`): https://github.com/nonara/ts-patch
- MS DevBlogs — Progress on TypeScript 7 ("Corsa", Dec 2025): https://devblogs.microsoft.com/typescript/progress-on-typescript-7-december-2025/
- VS Magazine — TS 6.0 ships as final JS-based release (2026-03-23): https://visualstudiomagazine.com/articles/2026/03/23/typescript-6-0-ships-as-final-javascript-based-release-clears-path-for-go-native-7-0.aspx
- typescript-eslint — `parserServices` / typed linting: https://typescript-eslint.io/getting-started/typed-linting/
