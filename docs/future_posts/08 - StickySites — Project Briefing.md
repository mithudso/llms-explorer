# StickySites — Project Briefing

**Version 1.10.0 · Chrome MV3 · Vanilla JS · No build step**

This document is a self-contained briefing for multiple audiences. Each section header marks its primary audience. Plain language is used in overview sections; precise technical terminology in developer- and reviewer-facing sections. All facts — commands, paths, versions, code references — are derived from actual repo files.

---

## 1. Executive Summary *(leadership)*

StickySites is a Chrome extension (Manifest V3) that puts sticky notes on every website. A floating, draggable icon cluster opens a moveable, resizable workspace panel with a rich-text editor; notes are scoped six ways — one global note, per-site, per-page, per-day, a per-site to-do list, and a per-site outliner. Everything is stored locally in the browser, with opt-in AES-256-GCM encryption at rest.

It is a **local, zero-dependency tool**. The packaged extension ships no third-party code and makes **no external network calls** — no telemetry, no accounts, no servers. All note content lives in `chrome.storage.local` on the user's machine. Built by Mitchell Hudson, it runs on vanilla JavaScript with no build step: Chrome reads the source directly, so a patch bump in `manifest.json` is the release.

Despite its small surface, it is maintained to a real engineering standard: 72 unit tests across three suites, a CI workflow, a complete documentation suite with a CI-validated file index, and a documented security model for the encryption feature.

---

## 2. Key Features *(all)*

- **Six note types** — Global (one shared note everywhere), Site (per domain), Page (per exact URL path), Daily (per calendar date), To-do (per-site checkbox list), and Outliner (a global library of named hierarchical documents).  
- **Floating icon cluster** — a draggable pill with one icon per note type, anchored to a saved position, with drag-to-reorder and a horizontal/vertical layout toggle. Icons carry identity hints (🌐 global, a domain fragment for site, the trailing path segment for page, day-of-month for daily) and refresh on SPA navigation.  
- **Workspace panel** — moveable (drag header) and resizable from any edge or corner, with an expand/shrink toggle and a popout button.  
- **19-tool rich-text editor** — bold/italic/underline/strikethrough, H1–H3, ordered/unordered lists, checkboxes, alignment, HR, indent/outdent, font family, font size, and a color picker, plus inline `#tags`. Find & Replace (`Cmd/Ctrl+F` / `Cmd/Ctrl+H`). Auto-saves 500 ms after the last keystroke.  
- **@-mention autocomplete** — type `@` for a caret-positioned dropdown across four categories: Link, Date, Contact, and File.  
- **Outliner** — keyboard-driven hierarchical outlines (Enter/Tab/Shift-Tab, Alt+↑/↓ move with subtree), zoom/hoist, collapse, per-node notes, drag-to-reorder, `#tag` chips, a filter box, Export to Markdown/OPML, and heuristic auto-group with undo.  
- **Popup dashboard** — full-text search across all notes, sort (Recent / Oldest / A–Z), filter by type or tag, a quick-open row, per-note or all-notes Markdown export, and a settings panel.  
- **Popout window** — open the current note in its own browser window via the ⧉ button or by dragging the panel off the page edge.  
- **Context-menu clipping** — right-click selected text to clip it into any of the six note types.  
- **Opt-in encryption at rest** — AES-256-GCM with a PBKDF2-derived key (600,000 iterations, SHA-256), enabled from the popup, with an in-page lock overlay.  
- **Hotkeys** — `Alt+S` toggles the cluster; `Ctrl/Cmd+F1`–`F6` open the six note types (these are dedicated function keys, so they never hijack ordinary typing).  
- **No build step, zero runtime dependencies** — the extension runs entirely on built-in `chrome.*` APIs and Web Crypto.

---

## 3. Problems Solved *(leadership + team)*

| Problem | What the extension does |
| :---- | :---- |
| **Notes scattered across apps** — context for a site lives in a separate notes app you have to switch to | Notes live on the page itself, scoped to the site, page, or day you're looking at |
| **One-size note scope** — a single notepad can't separate "this page" from "this site" from "today" | Six distinct scopes, each with its own storage key and resolver |
| **Losing notes on SPA navigation** — single-page apps change the URL without a reload | The panel snapshots the active key at open and re-keys safely on `popstate`/`hashchange`/href-poll |
| **Sensitive notes in plaintext** | Opt-in AES-256-GCM encryption with a PBKDF2-derived key and an in-page lock |
| **Hotkeys hijacking the page** | Bare-key shortcuts were removed; note-type shortcuts now require Ctrl/Cmd (`F1`–`F6`) so they never break page typing or select-all |
| **Finding a note later** | A popup dashboard with full-text search, sort, type/tag filters, and Markdown export |
| **Capturing text while reading** | Right-click context-menu clipping into any note type |
| **Privacy concerns with note tools** | Local-only storage, zero external calls, no telemetry, no third-party scripts |

---

## 4. Scope of Work *(leadership + reviewers)*

Built by Mitchell Hudson as an independent Chrome extension. Vanilla JavaScript, no build step, MIT-licensed. Line counts are raw `wc -l` at v1.10.0 (scope indicators, not SLOC).

| Component | Path | Approx. lines |
| :---- | :---- | :---- |
| Workspace panel + rich-text editor | `src/content/panel.js` | 1,848 |
| Outliner UI | `src/content/outline.js` | 800 |
| Storage CRUD (shared module) | `src/shared/notes-storage.js` | 363 |
| Other content scripts (cluster, mentions, todo, outline-ops, crypto-content, note-types, prefs, orchestrator) | `src/content/*` | ~1,274 |
| Service worker | `src/background/service-worker.js` | 86 |
| Crypto primitives (shared module) | `src/shared/crypto.js` | 71 |
| Popup dashboard | `popup.js` | 869 |
| Popout window | `popout.js` | 41 |
| Unit tests (3 suites) | `tests/*.js` | 572 |

**Engineering quality markers:**

- **CI.** `.github/workflows/test.yml` runs on push/PR to `main`: `npm ci`, `npm test`, and `npm run docs:check` (file-index integrity) on the Node version pinned in `.nvmrc`.  
- **Tests.** 72 unit tests across three suites — `crypto`, `notes-storage`, `outline-ops` — run with Vitest in a node environment, mocking `chrome.*` APIs. Pure logic (`outline-ops.js`, storage CRUD, crypto primitives) is extracted specifically to be testable.  
- **Documentation suite.** Architecture, components, security, testing, development, installation, logging, caching, external-calls, integrations, known-issues, onboarding, and requirements docs, plus two runbooks and a machine-readable `high_signal_file_index.json` validated in CI.  
- **No build step.** Chrome loads the source directly; `manifest.json.version` is the canonical release artifact (kept in sync with `package.json`).

---

## 5. Security Posture *(reviewers + leadership)*

**Summary for reviewers**: Minimal permissions, no broad host grants, zero external calls, no telemetry. Notes can be encrypted at rest with AES-256-GCM. The one nuance worth knowing: once unlocked, the derived key is cached in `chrome.storage.local` and persists on disk until the user locks — convenience over a session-only posture.

### Permissions

The manifest requests only `storage`, `activeTab`, and `contextMenus`. There are **no `host_permissions`** and no `tabs`, `webRequest`, `cookies`, `history`, or `identity` permissions. Content scripts do match `<all_urls>` — that breadth is inherent to "sticky notes on every site" — but the extension never reads or transmits page content off-device.

### Encryption at rest (opt-in)

- **Cipher:** AES-256-GCM; 12-byte random IV per operation; envelope `{ iv, data }`.  
- **Key derivation:** PBKDF2, 600,000 iterations, SHA-256, 16-byte random salt. The passphrase is never stored; a verification blob in `stickysites_crypto_v1` detects a wrong passphrase.  
- **Key cache (important):** the derived key is exported as JWK and cached in `chrome.storage.local` under `stickysites_cached_key` (and in memory). It **persists across browser restarts** until the user clicks **Lock Now** or disables encryption — it is *not* cleared on browser close. This trades a stronger session-only posture for not re-entering the passphrase each session.  
- Encryption covers only the six note storage keys; prefs are not encrypted.

### Other controls

- Context-menu selection text is HTML-entity-escaped before insertion into rich-text bodies.  
- Zero external network calls, no OAuth/identity APIs, no analytics, no third-party scripts, CDN resources, or external iframes (`docs/external-calls.md`).  
- `chrome.storage.local` is isolated per extension; other extensions cannot read it.

### What it does not defend against

- **No Shadow DOM encapsulation** — injected UI shares the host page's DOM, so aggressive host-page CSS can break the UI and host-page JavaScript can read the open panel's contents.  
- **A profile-level attacker while unlocked** — the cached key sits in extension storage on disk until locked.  
- In-memory plaintext is exposed while a note panel is open.

Full threat model, permissions audit, and key lifecycle: [`docs/SECURITY.md`](docs/SECURITY.md).

---

## 6. Architecture Overview *(reviewers + team)*

A Manifest V3 extension with a deliberate module-system split.

```
Browser action popup (popup.*) ─┐
Popout window (popout.*) ────────┤  chrome.runtime.sendMessage
                                 ▼
                        service worker (ES module)  ── src/background/service-worker.js
                         - context menus (6 types)     - Alt+S toggle command
                         - popout window creation       - storage.session.setAccessLevel
                                 ▲
        chrome.runtime.sendMessage │  (STICKYSITES_TOGGLE / OPEN / CLIP / POPOUT)
                                 ▼
content scripts (classic, ordered) ── src/content/*  → window.StickySites.*
  crypto-content → note-types → prefs → cluster → todo → outline-ops →
  outline → mentions → panel → sticky-inject (orchestrator)
                                 │
                                 ▼
        chrome.storage.local  (8 versioned keys + cached key)
        ↕ storage.onChanged → cross-tab live sync
```

### Module-system split (the central rule)

- **Content scripts** (`src/content/*`) load as **classic scripts** in the order declared in `manifest.json`; they cannot use ES `import` and instead attach to the global `window.StickySites.*` namespace. Load order matters — later scripts depend on earlier ones.  
- **Service worker** (`src/background/service-worker.js`) is an **ES module**.  
- **Shared modules** (`src/shared/*`) are ES modules used by the service worker and by Vitest. `crypto-content.js` (namespace) and `crypto.js` (ES module) are deliberate duplicates of the same AES-GCM algorithm.

### Storage

`chrome.storage.local` holds eight versioned keys — `stickysites_global_v1`, `_sites_v1`, `_pages_v1`, `_todos_v1`, `_outlines_v1`, `_daily_v1`, `_prefs_v1`, `_crypto_v1` — plus `stickysites_cached_key`. Records use a canonical `key` + `label` schema with fallbacks to legacy field names written before v1.10. `chrome.storage.session` is used only for the service worker's startup `setAccessLevel` call.

### Message contract

| Type | Direction | Purpose |
| :---- | :---- | :---- |
| `STICKYSITES_TOGGLE` | SW → content | Toggle cluster visibility |
| `STICKYSITES_OPEN` | SW → content | Open a specific note type (optional `key` targets an outline doc) |
| `STICKYSITES_CLIP` | SW → content | Clip selected text into a note |
| `STICKYSITES_POPOUT` | content → SW | Open the current note in a standalone window |

Full diagrams and design decisions: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## 7. Installation & Quick Start *(new users)*

### Install (load unpacked)

1. Clone this repository.  
2. Open `chrome://extensions` and enable **Developer mode**.  
3. Click **Load unpacked** and select the repo root.  
4. Click the StickySites toolbar icon or press **Alt+S** on any page.

There is no build step — Chrome reads the source directly.

### Development

```shell
npm install          # dev dependencies (Vitest, canvas)
npm test             # run unit tests (single pass)
npm run test:watch   # watch mode
npm run docs:check   # validate docs/high_signal_file_index.json
```

Requires **Node ≥ 22** for the test harness. Tests run in a node environment and mock `chrome.*` APIs. Full setup and troubleshooting: [`docs/INSTALLATION.md`](docs/INSTALLATION.md) and [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md).

---

## 8. Usage Guide *(team + new users)*

### Everyday use

- **Open a note:** click an icon in the floating cluster, or press `Ctrl/Cmd+F1`–`F6` (Global, Site, Page, To-do, Outline, Daily). `Alt+S` shows or hides the cluster.  
- **Write:** type in the panel; formatting toolbar across two rows; `#tags` inline; auto-saves after 500 ms. `Cmd/Ctrl+F` opens Find & Replace.  
- **Clip text:** select text on a page, right-click → **StickySites** → choose a note type.  
- **Pop out:** click ⧉ in the panel header, or drag the panel off the edge of the page.  
- **Find a note later:** open the toolbar popup → search, sort, filter by type or tag, export.

### Encryption

Open the popup **Settings** panel and enable encryption with a passphrase. All six note types are re-encrypted in place. Use **Lock Now** to clear the cached key; you'll re-enter the passphrase to unlock. (See §5 for the key-persistence nuance.)

---

## 9. Dependencies *(reviewers)*

### Runtime — none

The shipped extension has **zero runtime dependencies**. It runs entirely on built-in browser APIs: `chrome.storage`, `chrome.runtime`, `chrome.tabs`, `chrome.contextMenus`, `chrome.commands`, `chrome.windows`, and the Web Crypto API (`crypto.subtle`).

### Development (`devDependencies` in `package.json`)

| Package | Version | Rationale |
| :---- | :---- | :---- |
| `vitest` | `^4.1.0` | Unit-test runner (node environment; `chrome.*` mocked) |
| `canvas` | `^3.2.3` | Used by `scripts/generate-icons.js` to render the extension icons |

---

## 10. Contribution & Workflow *(team)*

### Workflow log

The repo keeps a committed operator log: append the user request to `prompts.md` and update the latest `memory.md` entry as work progresses. (A separate, gitignored `.remember/` directory is used by local tooling; `memory.md`/`prompts.md` are the shareable record.)

### Version bump

`manifest.json.version` is canonical and is the release. Bump the patch there and keep `package.json.version` in sync on any meaningful change.

### Where things go

- New content-script logic → `src/content/*` on the `window.StickySites.*` namespace; keep the `manifest.json` load order correct (later scripts depend on earlier namespaces).  
- Worker-side logic → `src/background/service-worker.js` (ES module); shared, testable logic → `src/shared/*`.  
- New external integration → there are none today, and adding one is a deliberate decision: preserve the zero-external-call property unless there is a strong reason not to.

### Validation gate

```shell
npm test && npm run docs:check
```

Both run in CI. Conventions: vanilla JS only (no frameworks/transpilers/bundlers); injected DOM uses the `stickysites-` prefix; storage keys are `_v1`-versioned; auto-save debounced at 500 ms.

---

## 11. Known Limitations *(all)*

See [`docs/known-issues.md`](docs/known-issues.md) for full detail.

| Limitation | Impact |
| :---- | :---- |
| **No Shadow DOM encapsulation** | Injected UI shares the host DOM; aggressive host-page CSS can break the StickySites UI, and host-page JS can read the open panel. A Shadow DOM root is the planned fix. |
| **Content-script re-injection on update** | Chrome may re-inject after an extension update; a guard prevents double UI, but listeners from the previous injection can be orphaned until the page is reloaded. |
| **PBKDF2 is slow on low-end devices** | 600 K iterations can take 2–4 s to unlock, with no progress indicator, so the unlock button appears to hang. By design (security floor); a spinner is the planned improvement. |
| **Cached key persists on disk until locked** | The derived key lives in `chrome.storage.local` until **Lock Now** or disable — not cleared on browser close (see §5). |
| **Rich-text editor uses `document.execCommand`** | The toolbar relies on the deprecated `execCommand` API; it works in current Chrome but is not future-proof. |

---

## Links

| Resource | Path |
| :---- | :---- |
| Architecture | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) |
| Components | [`docs/COMPONENTS.md`](docs/COMPONENTS.md) |
| Security model | [`docs/SECURITY.md`](docs/SECURITY.md) |
| Development | [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) |
| Installation | [`docs/INSTALLATION.md`](docs/INSTALLATION.md) |
| Testing | [`docs/TESTING.md`](docs/TESTING.md) |
| Logging | [`docs/logging.md`](docs/logging.md) |
| Caching & optimization | [`docs/caching-and-optimization.md`](docs/caching-and-optimization.md) |
| External calls (none) | [`docs/external-calls.md`](docs/external-calls.md) |
| Known issues | [`docs/known-issues.md`](docs/known-issues.md) |
| Codebase overview | [`docs/codebase-overview.md`](docs/codebase-overview.md) |
| File index (machine-readable) | [`docs/high_signal_file_index.json`](docs/high_signal_file_index.json) |
| Runbooks | [`docs/runbooks/`](docs/runbooks/) |
| Bootstrap audit (2026-06-17) | [`docs/repo-bootstrap-audit-2026-06-17.md`](docs/repo-bootstrap-audit-2026-06-17.md) |

---

*Last updated: 2026-06-17 · v1.10.0*

---