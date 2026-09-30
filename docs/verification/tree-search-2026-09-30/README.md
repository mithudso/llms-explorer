# Concept-tree search verification

Version: 1.0.0. Date: 2026-09-30. Site: 0.0.9.

The clean-browser reproduction failed with zero search results. The ONNX runtime module was rewritten to a blob URL that the CSP rejected. Transformers WASM module caching is now disabled, and ONNX uses one thread. Model caching remains enabled. Only the exact `/tree/` route permits WebAssembly compilation; it still rejects arbitrary JavaScript evaluation and blob scripts.

Cloudflare also injected a changing inline challenge script after the build. The Pages Function adds a fresh 128-bit nonce to the response CSP for tree HTML. It preserves authored-script hashes and other routes. Cloudflare documents that it copies a response-header nonce to its injected JavaScript Detection script:
https://developers.cloudflare.com/cloudflare-challenges/challenge-types/javascript-detections/#if-you-have-a-content-security-policy-csp

Search handlers catch focus, loading and inference failures. Failed downloads retry after input changes. Backend initialization or inference failures can require a reload because the locked runtime retains rejected promises; the status messages state that limit. Input changes invalidate earlier queries immediately. The plain Filter now initializes after its list exists.

The built release passed 264 site tests, Astro check (zero errors, zero warnings, 26 existing hints), and the llms lint gate (zero High findings). Nine focused async/nonce tests passed after the final error-message correction. The source-executing search scenarios independently fail against the original component. Independent review found the recovery-message issue, which was corrected.

Chrome 154 returned eight real semantic matches for “How does prompt caching reduce token cost?”, led by “Prompt caching”. Filtering “caching” matched nine concepts, hid unrelated branches, and reset cleanly. An intercepted first index download returned 503; the next query recovered with eight results and no unhandled promise. The browser logged no errors or CSP violations. It loaded the locked ONNX module directly from the versioned HTTPS URL. `local-browser.json` contains the receipt.

The reported `Unexpected end of input` and React toolbar #130 did not reproduce in clean Chrome. Authored inline scripts and embedded JSON parse successfully. The toolbar script was absent from the raw page. This change does not claim to repair those unconfirmed errors.

The release branch starts at deployed `origin/main` (`be3879f`) and carries only this search fix, tests, version and continuation records. It preserves the shared checkout's unpublished history and other working edits. No indexing or Ollama process was started and no search vectors were regenerated.

Run from the repository root after a production build:

```sh
node site/tests/e2e/tree-search.mjs
TREE_SEARCH_URL=https://llms-explorer.com/tree/ node site/tests/e2e/tree-search.mjs
```

The browser test prints a JSON receipt and exits zero only if real results, filtering, download recovery and CSP checks pass. Set `CHROME_BIN` to a Chrome executable on non-macOS hosts. It downloads the normal browser model and uses its cache.

The complete user report is in `prompt.txt`. Structured checks are in `verification.json`. CI, merge, deployed acceptance and remaining publication steps are recorded in the live task:
https://app.stele-ai.dev/p/llms-explorer-9d1wd/nodes/TASK-85
