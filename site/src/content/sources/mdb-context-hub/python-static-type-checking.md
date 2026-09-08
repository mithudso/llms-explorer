---
title: "Python Static Type Checking"
description: "> Reference file — part of the programming-languages hub. Authored via /dr (deep-research). Not a standalone skill."
---

<!-- hub-reference-banner -->
> **Reference file — part of the `programming-languages` hub.** Authored via `/dr` (deep-research). Not a standalone skill.
> Sibling topics in this family are reference files under the hubs (`programming-languages`, `software-engineering-patterns`) — **not** standalone skills.
> Cross-refs: `references/python-patterns.md` (PEP 695 type-hint *syntax*, generics — this file covers the *checkers*), `references/pydantic-v2.md` (runtime validation + the `pydantic.mypy` plugin), `references/typescript-expert.md` (the TS analog of gradual static typing).

# Python Static Type Checking — mypy, Pyright, ty, Pyrefly

Python type checkers are **external static-analysis tools**, not part of the interpreter. The CPython runtime ignores annotations (beyond storing them in `__annotations__`); a separate tool reads the same annotations a human reads and proves type consistency *before* the code runs.

As of mid-2026 the landscape is a **two-generation split**: established Python-implemented checkers (**mypy**, **Pyright**) and new **Rust-implemented** checkers (**Astral ty**, **Meta Pyrefly**) that are 10-80x faster. Pyrefly reached stable **1.0.0 (May 2026)**; ty is still **beta (0.x)**.

## 1. Shared foundation: gradual typing
- **PEP 483 + PEP 484 (2015)** define *gradual typing*: hints are optional, coexist with dynamic typing, added incrementally. Goal is NOT runtime enforcement — annotations exist for external tools.
- **`Any`** is consistent with every type (assignable to/from anything) — the seam between static and dynamic. Unannotated code is effectively `Any`.
- **The gradual guarantee:** removing an annotation should never add new errors (adding annotations only narrows errors). ty and Pyright honor it strictly; mypy and Pyrefly infer aggressively and can violate it.
- **PEP 561:** inline-typed packages ship a **`py.typed`** marker; stub-only packages are **`types-<pkg>`** (types-requests) or **`<pkg>-stubs`**; stub files are **`.pyi`**; resolution order stubs → inline → **typeshed** (the community stub repo).
- **typing-spec conformance suite** is the shared benchmark. Pyrefly 1.0.0 reports >90% (above ty and mypy); Pyright tracks the spec closely.
- *Declared* types (you annotated) vs *inferred* types (deduced) — checkers agree on declared, disagree on inference (§3).

## 2. The four checkers

| | mypy | Pyright | ty | Pyrefly |
|---|---|---|---|---|
| Author | community | Microsoft | Astral (uv/ruff) | Meta |
| Language | Python (mypyc) | TS/Node | **Rust** | **Rust** |
| Maturity 2026 | mature, ref impl | mature | **beta 0.x** | **stable 1.0.0** |
| Unannotated funcs | **skips** | **checks** | checks | checks |
| Inference | aggressive `list[int]` | conservative `list[Unknown]` | conservative, gradual guarantee | aggressive `list[int]` |
| Config table | `[tool.mypy]`/`mypy.ini` | `[tool.pyright]` | `[tool.ty]` | `[tool.pyrefly]` |
| Extensibility | **plugins** + stubs | stubs only | stubs | stubs |
| LSP | none built-in | **Pylance** (best) | full LSP | full LSP + infer-to-source |
| Speed | baseline | varies | **fastest ~80x** | ~2-3x slower than ty |
| Novel | — | early PEP | **intersection & negation types** | strong generic inference |

CLI: `mypy <path>`, `pyright <path>`, `ty check <path>`, `pyrefly check <path>`.

## 3. Inference divergence (the key behavioral difference)
For `my_list = []; my_list.append(1)`:
- **mypy, Pyrefly** infer `list[int]` from usage → later `append("foo")` is an **error**.
- **Pyright, ty** infer `list[Unknown]`, stay permissive → `append("foo")` **allowed** (gradual guarantee).

Generics: `c: C[int] = C()` reveals `C[int]` (Pyrefly) vs `C[Unknown]` (ty). mypy/Pyrefly catch more bugs in loose code but more false positives; Pyright/ty cause fewer surprises during adoption. `reveal_type(x)` prints inferred type during a check.

## 4. mypy (reference impl)
- **Skips unannotated function bodies by default** (#1 gotcha) — `--check-untyped-defs` or `--strict` to check inside them.
- `--strict` bundles all optional checks. Key flags: `disallow_untyped_defs`, `disallow_incomplete_defs`, `disallow_any_generics`, `warn_return_any`, `warn_unused_ignores`, `no_implicit_optional`.
- Config: `mypy.ini` / `setup.cfg` / `[tool.mypy]`. Per-module `[[tool.mypy.overrides]]` for strict-by-default, loose-for-legacy:
```toml
[tool.mypy]
strict = true
plugins = ["pydantic.mypy"]
[[tool.mypy.overrides]]
module = ["legacy.*"]
disallow_untyped_defs = false
ignore_missing_imports = true
```
- **Plugins (unique to mypy):** understand dynamic patterns (ORMs, metaclasses) — `pydantic.mypy`, `sqlalchemy.ext.mypy.plugin`. mypy 2.0 added `--num-workers` (~1.3x).

## 5. Pyright (conservative, IDE-first)
- **Checks all code by default** (opposite of mypy). **Five strictness levels:** `off`/`basic`/`standard`(default)/`strict`/`all`. `strict` adds ~30 rules, ~10x more errors than basic.
- Per-rule `reportXxx` keys = `"none"|"warning"|"error"` (e.g. `reportUnknownMemberType`). Config `[tool.pyright]` or `pyrightconfig.json`.
- **No plugins** (stubs only). Powers **Pylance** (closed-source VS Code, best-in-class). **BasedPyright** = OSS fork, stricter defaults. Suppress: `# pyright: ignore[reportXxx]`.

## 6. ty (Astral, beta)
- uv/ruff team; Rust; **Salsa** fine-grained incremental engine → re-diagnoses a PyTorch file in ~4.7ms (~80x faster than Pyright's ~386ms).
- Conservative inference (`Unknown` type) + strict gradual guarantee. **Only checker with intersection & negation types** (`MyClass & ~MySubclass`). Concise/structured errors.
- **beta, 0.0.x, no stable API** — diagnostics can change between releases. Config `[tool.ty]`; full LSP (VS Code/Neovim/Zed/PyCharm). Roadmap: ruff/uv integration. CLI `ty check`.

## 7. Pyrefly (Meta, stable 1.0.0)
- Rust **successor to Pyre** (Instagram's OCaml checker). MIT, open-sourced May 2025; **stable 1.0.0 May 2026**. Module-level incremental + multithreaded.
- **Aggressive inference** (mypy camp), strong generics. **`pyrefly infer`** writes inferred annotations directly into source (migration accelerator no other checker has).
- Instagram (~20M LOC) in 13.4s; PyTorch ~2.4s. **Conformance >90%** (above ty/mypy). Adoption at PyTorch, JAX. Config `[tool.pyrefly]`; CLI `pyrefly check`.

## 8. Choosing
- **Existing project / established CI:** mypy (plugins, maturity).
- **Best VS Code:** Pyright/Pylance or BasedPyright (OSS, stricter).
- **New project, max catch + speed, OK with aggressive inference:** Pyrefly (stable, highest conformance).
- **Predictable incremental adoption + fastest, tolerate beta:** ty.
- **CI:** run a Rust checker as the fast gate; don't run two strict checkers as blocking gates (their inference disagreements fight).

## 9. Migrating an untyped codebase
1. Start permissive, ratchet strictness from a clean baseline.
2. Strict-by-default, loose-for-legacy via per-module overrides.
3. Fix missing third-party types: install `types-<pkg>` or scope `ignore_missing_imports` — don't blanket-ignore.
4. Auto-annotate with `pyrefly infer`, then review.
5. Ship `py.typed` (PEP 561) so downstream trusts your inline types.
6. Gate in CI once clean; track error count downward.

## 10. Anti-patterns
- Trusting mypy's default coverage (it skips unannotated bodies — green can mean "nothing checked").
- Blanket `# type: ignore` — scope it (`# type: ignore[arg-type]`); set `warn_unused_ignores`.
- Two strict checkers as blocking gates (inference disagrees).
- Expecting runtime enforcement — checkers never run code; for runtime validation use **Pydantic v2**.
- `Any` creep — prefer `object`/`Protocol`/precise union; `disallow_any_generics`/`warn_return_any`.
- Assuming ty diagnostics are stable (0.x — pin the version).

## 11. Troubleshooting
- "missing library stubs" → install `types-<pkg>` or scope `ignore_missing_imports`; check for `py.typed`.
- "works in mypy, errors in Pyright" → inference divergence (§3) or mypy-plugin behavior Pyright can't replicate. No parity.
- Slow mypy → incremental cache (default on), `--num-workers`, or move fast gate to ty/Pyrefly.
- Pydantic/SQLAlchemy "untyped" on Pyright/ty/Pyrefly → those rely on mypy *plugins*; use native typing (Pydantic v2 is natively typed).
- Error flood after strict → expected (Pyright strict ≈ 10x basic); ratchet per-module.

## References
- PEP 483 — https://peps.python.org/pep-0483/ · PEP 484 — https://peps.python.org/pep-0484/ · PEP 561 — https://peps.python.org/pep-0561/
- mypy config — https://mypy.readthedocs.io/en/stable/config_file.html
- Pyright mypy-comparison — https://github.com/microsoft/pyright/blob/main/docs/mypy-comparison.md
- ty repo — https://github.com/astral-sh/ty · ty beta — https://pydevtools.com/blog/ty-beta/
- mypy/pyright/ty compare — https://pydevtools.com/handbook/explanation/how-do-mypy-pyright-and-ty-compare/
- Meta Pyrefly (InfoQ) — https://www.infoq.com/news/2025/05/meta-pyrefly-python-typechecker/
- Pyrefly vs ty (Edward Li) — https://blog.edward-li.com/tech/comparing-pyrefly-vs-ty/
- Pyrefly/ty (InfoWorld) — https://www.infoworld.com/article/4005961/pyrefly-and-ty-two-new-rust-powered-python-type-checking-tools-compared.html
- Conformance deep dive — https://sinon.github.io/future-python-type-checkers/
