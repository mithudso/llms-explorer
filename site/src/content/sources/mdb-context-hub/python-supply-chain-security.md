---
title: "Python Supply-Chain & Application Security"
description: "Python application security splits into two layers that share one toolchain:"
---

# Python Supply-Chain & Application Security

## Overview

Python application security splits into two layers that share one toolchain:

1. **Application security (SAST)** — find vulnerabilities in *your own code* (bandit).
2. **Supply-chain security** — defend the dependencies and the path your artifacts travel: know what you ship (SBOM), know if it is vulnerable (pip-audit), prove where it came from (sigstore/PEP 740 attestations), and guarantee you install exactly what you locked (hash pinning).

The canonical layered ("defense in depth") posture for a 2026 Python project: **pin + hash** dependencies → **audit** them in CI (`pip-audit`) → **SAST-scan** your code (`bandit`) → **generate an SBOM** → **publish with Trusted Publishing + attestations**. Each layer closes a gap the others cannot; none is sufficient alone (hash pinning, for example, will faithfully pin a package that was *already* malicious on day one).

The four foundational PyPA/PyCQA tools — `pip-audit`, `bandit`, `pip` hash mode, and the PEP 740 attestation chain — are free, open source, and require no account or API key for the scanning paths.

## Core Concepts

### 1. Dependency auditing — pip-audit
- **What it is:** the official PyPA tool that audits Python environments, `requirements` files, and dependency trees for packages with **known** vulnerabilities (SCA — software composition analysis). Maintained by the Python Packaging Authority.
- **Vulnerability sources:** queries the **PyPA Advisory Database** and the **OSV** database. Select via `--vulnerability-service {osv,pypi}` (osv is default); `--osv-url` points at a custom OSV mirror.
- **Input modes:** audit the live environment (`pip-audit`), a requirements file (`pip-audit -r requirements.txt`), or a **PEP 751 lockfile** (`pylock.toml`, supported in recent releases). For fully pinned input, skip resolution with `--no-deps` (pinned, no hashes) or `--require-hashes` (pinned + hashed).
- **Auto-fix:** `--fix` upgrades vulnerable pins in place to the first non-vulnerable version; `--dry-run` previews.
- **Output / SBOM:** `-f {columns,json,cyclonedx-json,cyclonedx-xml,markdown}` — it can itself emit a CycloneDX SBOM with vulnerabilities linked to affected components via the `affects` field.

### 2. SBOM generation (Software Bill of Materials)
- **Why:** a machine-readable inventory of every component (incl. transitive) so downstream consumers and scanners can answer "am I affected by CVE-X?" Increasingly required by regulation (US EO 14028, EU Cyber Resilience Act).
- **Two formats:**
  - **CycloneDX** — security-first; built for vulnerability identification and outdated-dependency analysis. Dominant in the Python ecosystem (of the ~1.6% of PyPI packages shipping an SBOM, effectively all are CycloneDX).
  - **SPDX** — license-compliance-first; richer license fields. ISO/IEC 5962 standard.
- **Tools:**
  - `cyclonedx-py` (the `cyclonedx-bom` distribution) — the most accurate Python-native generator; reads environments, `requirements.txt`, `poetry.lock`, `Pipfile.lock`, and pip lockfiles with proper hash support. Subcommands: `cyclonedx-py environment`, `... requirements`, `... poetry`.
  - `uv export --format cyclonedx` — straight from `uv.lock` (see `references/uv-python-toolchain.md`).
  - **Syft** (Anchore) — ecosystem-agnostic; SBOMs from filesystems/container images; emits both CycloneDX and SPDX. Use for the *container* layer.
  - `lib4sbom` — parse/convert SBOMs between SPDX and CycloneDX.
- **PEP 770 (SBOMs inside wheels):** standardizes shipping SBOMs in a wheel's `.dist-info/sboms/` directory, so consumers get the SBOM automatically on `pip install`. Solves the "phantom dependency" problem (bundled non-Python libs invisible to Python-level tools).

### 3. Static application security testing — bandit
- **What it is:** the PyCQA SAST linter for Python. Builds an **AST** per file and runs security plugins against it. Catches insecure patterns *before* runtime.
- **B-codes (rule families):** B1xx general (B101 `assert`, B102 `exec`, B105/B106/B107 hardcoded passwords, B108 temp-file); B3xx blacklisted calls/imports (B301 `pickle`, B303/B304 weak MD5/SHA1 / insecure ciphers, B307 `eval`, B311 non-crypto `random`); B5xx crypto/cert (B501 `verify=False`); B6xx injection (B602 `subprocess` with `shell=True`, B608 SQL string-build); plus newer AI/ML checks (B614 unsafe `torch.load`, B615 insecure Hugging Face download).
- **Severity × confidence:** every finding has a **severity** (LOW/MEDIUM/HIGH) and a **confidence** (how sure bandit is it is real). Filter both: `--severity-level medium --confidence-level medium` is the standard noise cut.
- **Config:** `[tool.bandit]` in `pyproject.toml` or a `.bandit` INI / `bandit.yaml` — set `exclude_dirs`, `skips` (e.g. `B101`), `tests` (allowlist), per-plugin options. Inline suppression: `# nosec B602` on the offending line (scope the code — bare `# nosec` is an anti-pattern).
- **Baseline workflow:** `bandit -r src/ -f json -o baseline.json`, then `bandit -r src/ -b baseline.json` so CI only flags **newly introduced** issues — the practical way to adopt bandit on a legacy codebase without a wall of red.

### 4. Provenance — sigstore, PEP 740 attestations & Trusted Publishing
- **The problem PGP couldn't solve:** PyPI deprecated/removed PGP signatures — almost nobody verified them and key management was broken. PEP 740 replaces them with **identity-based** signing.
- **Trusted Publishing (OIDC):** instead of a long-lived API token, a CI workflow (GitHub Actions, GitLab CI, etc.) presents a short-lived **OIDC identity** to PyPI and receives a short-lived upload token. No secret to leak/rotate. This is the prerequisite layer.
- **PEP 740 digital attestations:** cryptographically signed, publicly verifiable statements about a package (notably **build provenance**). Built on **Sigstore** with **short-lived signing keys bound to the OIDC identity** (keyless signing → Rekor transparency log), and the payload follows the **in-toto Attestation Framework**. Because there is no private key sitting around, key loss/theft is largely designed out.
- **How to get it:** if you already publish via Trusted Publishing with `pypa/gh-action-pypi-publish` **v1.11.0+**, build provenance attestations are generated and uploaded **automatically** — usually zero code change. PyPI exposes attestations + Trusted-Publishing metadata as **provenance objects** through the HTML and JSON Simple APIs.
- **Verification:** the `pypi-attestations` CLI / library verifies a downloaded file's attestation against the expected identity. Track ecosystem adoption at the "Are we PEP 740 yet?" dashboard.

### 5. Hash-pinned dependencies (reproducible, tamper-evident installs)
- **What it does:** records a cryptographic digest (`--hash=sha256:…`) for every artifact. On install, pip recomputes and compares; a mismatch **aborts the install**.
- **What it protects against:** tampering in transit, in a cache, or on a compromised mirror; a PyPI or TLS-chain compromise; a package whose *content* changes without a version bump. It is the integrity backstop.
- **What it does NOT protect against:** a package that is malicious from the first install (you just pin the malicious hash), and it says nothing about *whether* a dependency is vulnerable (that's `pip-audit`'s job).
- **Generating hashes:**
  - `pip-tools`: `pip-compile --generate-hashes requirements.in` → fully pinned `requirements.txt` with `--hash` lines.
  - `uv`: `uv lock` (hashes in `uv.lock`) or `uv pip compile --generate-hashes` / `uv export --format requirements-txt` (see `references/uv-python-toolchain.md`).
  - Pipenv records hashes in `Pipfile.lock` natively.
- **Enforcing:** `pip install --require-hashes -r requirements.txt`. `--require-hashes` is auto-enabled if any line has a hash; it then demands **every** requirement be pinned (`==`) and hashed, including transitive deps — which is why a hash-generating compiler is mandatory.

## Tools / Frameworks (quick map)

| Need | Tool | Note |
| --- | --- | --- |
| Audit deps for known CVEs | `pip-audit` | PyPA; OSV + PyPA Advisory DB |
| SAST on your code | `bandit` | PyCQA; AST plugins, severity×confidence |
| SBOM (Python project) | `cyclonedx-py` / `uv export --format cyclonedx` | CycloneDX, hash-aware |
| SBOM (container/filesystem) | `syft` | CycloneDX **or** SPDX |
| Provenance / signing | Trusted Publishing + PEP 740 attestations | Sigstore keyless, auto via gh-action-pypi-publish ≥1.11.0 |
| Verify attestations | `pypi-attestations` | identity-bound verification |
| Hash pinning | `pip-compile --generate-hashes` / `uv lock` + `pip install --require-hashes` | reproducible, tamper-evident |
| Repo/workflow security score | **OpenSSF Scorecard** (`scorecard` CLI / Action) | health metrics + risk checks |
| Harden GitHub Actions workflows | **zizmor** | flags `pull_request_target` misuse, unpinned third-party actions, secret handling |
| 3rd-party SCA (commercial/alt) | Snyk, Safety, Trivy, Grype, Dependabot/Renovate | overlap with pip-audit; Trivy/Grype also scan containers |

## Methodology — layered project posture

1. **Lock + hash** every dependency (`uv lock` or `pip-compile --generate-hashes`); install with `--require-hashes` (`uv sync` enforces the lock).
2. **Audit in CI** — `pip-audit -r requirements.txt` (or against the lockfile); fail the build on findings; use `--fix --dry-run` to triage upgrades. Do **not** auto-update to latest blindly.
3. **SAST in CI** — `bandit -r src/ -c pyproject.toml`; run **HIGH-severity only** as a blocking gate, full set as non-blocking/local; adopt via a baseline.
4. **Generate an SBOM** as a build artifact (`cyclonedx-py` for the app, `syft` for the image); attach to the release; PEP 770 to embed in wheels you publish.
5. **Publish with provenance** — Trusted Publishing (OIDC, no token) + automatic PEP 740 attestations via `gh-action-pypi-publish`.
6. **Harden the pipeline itself** — pin third-party Actions to a full commit SHA, run **zizmor** on workflows, track posture with **OpenSSF Scorecard**. The supply chain includes your *CI*, not just your deps.

## Practical Patterns

```bash
# CI audit gate (non-zero exit fails the build)
pip-audit -r requirements.txt --strict --desc

# Audit a PEP 751 lockfile and emit a CycloneDX SBOM at the same time
pip-audit -r pylock.toml -f cyclonedx-json -o sbom.json

# bandit: blocking HIGH gate in CI, configured from pyproject
bandit -r src/ -c pyproject.toml --severity-level high --confidence-level medium

# bandit baseline adoption on a legacy repo
bandit -r src/ -f json -o .bandit-baseline.json   # once, on a clean-enough commit
bandit -r src/ -b .bandit-baseline.json            # every PR: only NEW issues fail

# generate fully hashed, pinned requirements, then enforce on install
pip-compile --generate-hashes -o requirements.txt requirements.in
pip install --require-hashes -r requirements.txt

# project SBOM (CycloneDX) from the current environment
cyclonedx-py environment -o sbom.cdx.json
```

```toml
# pyproject.toml
[tool.bandit]
exclude_dirs = ["tests", ".venv", "build"]
skips = ["B101"]            # asserts are fine in tests; scope properly instead of blanket-skipping in src
# severity/confidence are passed as CLI flags, not config keys
```

```yaml
# .github/workflows/release.yml — Trusted Publishing + automatic PEP 740 attestations
permissions:
  id-token: write            # REQUIRED for OIDC Trusted Publishing + attestations
jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<full-commit-sha>   # pin 3rd-party actions to a SHA
      # ... build sdist + wheel ...
      - uses: pypa/gh-action-pypi-publish@release/v1   # ≥1.11.0 → provenance by default
        # no password/token needed: PyPI is configured as a Trusted Publisher for this repo
```

## Anti-Patterns

- **Trusting hash pinning to vet packages.** Hashes guarantee *integrity*, not *safety*. Pair with `pip-audit` (known CVEs) and review for first-time deps.
- **Blanket `# nosec`** with no rule code — silently suppresses *all* future findings on that line. Always `# nosec Bxxx`.
- **Running bandit at default severity in CI** — B101 assert noise drowns real findings; teams disable the whole tool. Filter to medium/high and use a baseline.
- **Long-lived PyPI API tokens in CI secrets.** Migrate to Trusted Publishing; a leaked token (cf. the 2025 GhostAction theft of 3,300+ secrets) is a full publish compromise.
- **Unpinned third-party GitHub Actions (`@v4`/`@main`).** A tag can be force-moved to malicious code. Pin to a full commit SHA; verify with zizmor.
- **Partial hashing.** `--require-hashes` requires *every* (incl. transitive) requirement pinned + hashed; a half-hashed file fails. Always regenerate via a compiler.
- **Generating an SBOM once and never again.** An SBOM is only useful if regenerated on every release and stored as an artifact you can query when a new CVE drops.
- **Auditing only direct dependencies.** Most CVEs and most supply-chain attacks ride in *transitive* deps; audit the full resolved tree/lockfile.

## Troubleshooting

- **`pip-audit` exits non-zero but you must ship now:** triage with `--fix --dry-run`; if a finding is a known false positive / unfixable, `--ignore-vuln <GHSA/PYSEC id>` (document why).
- **`pip install --require-hashes` fails "hashes are required for all packages":** a transitive dep is unpinned/unhashed — regenerate with `pip-compile --generate-hashes` or `uv export`.
- **Hash mismatch on install:** the artifact differs from the locked hash — could be a mirror/cache problem **or** tampering. Do not bypass; re-resolve from PyPI and compare.
- **bandit flags `B608` SQL or `B602` subprocess you know is safe:** restructure to remove the pattern (parameterized query, `shell=False` + list args) rather than suppress — the rule is usually right.
- **Attestations not appearing on PyPI:** confirm `permissions: id-token: write`, `gh-action-pypi-publish` ≥ 1.11.0, and that the repo is registered as a Trusted Publisher (not token auth).
- **SBOM missing bundled native libs ("phantom dependencies"):** Python-level generators can't see vendored C libs; use Syft on the built artifact/image, and adopt PEP 770 for wheels you publish.

## 2025-2026 threat landscape (why this matters)

- **Typosquatting & dependency confusion** remain the top vectors: malicious packages named like `requests`/`tensorflow` (500+ typosquats in waves), and internal-name confusion pulling a public package over a private one.
- **2025 PyPI phishing** — `noreply@pypj.org` (note the `j`) proxy credential harvester targeting maintainers.
- **GhostAction (Sept 2025)** — injected workflows across 570+ repos, exfiltrating 3,300+ secrets incl. PyPI/npm/AWS tokens — the canonical case for Trusted Publishing over tokens and for pinning/auditing CI.
- **Shai-Hulud worm (Nov 2025)** — cross-ecosystem (npm-origin) worm that also hit PyPI via monorepos sharing credentials.
- PyPI processed **2,000+ malware reports in 2025**, 66% within 4 hours — fast, but reactive; your pinning + audit + provenance layers are the proactive defense.

## References (sources)

- pip-audit — https://github.com/pypa/pip-audit · https://pypi.org/project/pip-audit/
- PyPA Advisory Database — https://github.com/pypa/advisory-database · OSV — https://osv.dev
- bandit — https://bandit.readthedocs.io · https://pypi.org/project/bandit/ (PyCQA)
- pip repeatable installs / `--require-hashes` — https://pip.pypa.io/en/stable/topics/repeatable-installs/
- pip-tools `--generate-hashes` — https://github.com/jazzband/pip-tools
- CycloneDX Python (`cyclonedx-py`) — https://github.com/CycloneDX/cyclonedx-python · https://cyclonedx-bom-tool.readthedocs.io
- Syft — https://github.com/anchore/syft · lib4sbom — https://pypi.org/project/lib4sbom/
- PEP 740 (digital attestations) — https://peps.python.org/pep-0740/ · PEP 770 (SBOMs in packages)
- PyPI attestations docs — https://docs.pypi.org/attestations/ · blog.pypi.org/posts/2024-11-14-pypi-now-supports-digital-attestations/
- Trail of Bits "Attestations: a new generation of signatures on PyPI" — https://blog.trailofbits.com/2024/11/14/attestations-a-new-generation-of-signatures-on-pypi/
- "Are we PEP 740 yet?" — https://trailofbits.github.io/are-we-pep740-yet/ · `pypi-attestations` — https://pypi.org/project/pypi-attestations/
- OpenSSF Scorecard — https://scorecard.dev · https://github.com/ossf/scorecard · ossf/malicious-packages
- zizmor (GitHub Actions SAST) — https://docs.zizmor.sh
- bernat.tech "Defense in Depth: A Practical Guide to Python Supply Chain Security"
- sbomify Python SBOM guide — https://sbomify.com/guides/python/
