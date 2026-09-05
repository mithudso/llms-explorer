# Runbook: scrubbing identifiers from git history

Prepared 2026-09-05. **Not yet executed — this rewrites public history and force-pushes.**

`scripts/check_publish_privacy.py` stops new identifiers reaching a published file, and
the current tree is clean. It cannot touch what is already committed. This runbook removes
identifiers from the history of a public repository.

Read the whole thing before running any of it. Step 6 is irreversible and step 8 is the
part people forget.

## When this is worth doing

Rewriting public history is disruptive: every commit SHA changes, open PRs break, and
everyone with a clone must re-clone. It is worth it when the exposed material is
identifying and durable — customer names, an operator's account, a case number — and not
worth it for a stale version number.

Be honest about the ceiling. **A rewrite does not un-publish anything.** Forks keep their
own objects, anyone who cloned still has it, and GitHub retains unreferenced objects until
asked to purge them. Treat this as reducing further exposure, not as undoing it. If the
material is genuinely sensitive, the rewrite is the second step; the first is telling
whoever owns the data.

## 0. Decide, and tell people first

Everyone with a clone loses their ability to `git pull` cleanly. Agree a window.

## 1. Inventory what to replace

The literals live in `.privacy-denylist`, which is gitignored precisely so they are not in
the repository. If you have not created it yet:

```bash
cp .privacy-denylist.example .privacy-denylist
# add one term per line: customer names, employer domains, the drive name, case numbers
```

Confirm the terms actually appear in history before rewriting anything:

```bash
while IFS= read -r term; do
  [ -z "$term" ] && continue
  case "$term" in \#*) continue ;; esac
  n=$(git log --all --oneline -S"$term" | wc -l | tr -d ' ')
  printf '%-40s %s commit(s)\n' "$term" "$n"
done < .privacy-denylist
```

A term with 0 commits does not need rewriting. A term with many may appear in prose you
still want, so check a sample with `git log --all -S"$term" -p | head -50` before deciding.

## 2. Back up

```bash
git bundle create ../llms-explorer-backup-$(date +%Y%m%d-%H%M%S).bundle --all
```

Verify it restores before continuing. A bundle you have not tested is not a backup:

```bash
git clone ../llms-explorer-backup-*.bundle /tmp/restore-test && \
  git -C /tmp/restore-test log --oneline -3 && rm -rf /tmp/restore-test
```

## 3. Install git-filter-repo

`git filter-branch` is deprecated and slow; `filter-repo` is the supported tool.

```bash
brew install git-filter-repo      # or: pipx install git-filter-repo
git filter-repo --version
```

## 4. Work on a fresh clone

`filter-repo` refuses to run on a repository with existing remotes unless forced, because
a rewrite on your working clone leaves it in a state that is easy to push by accident.
Give it a clone of its own:

```bash
cd /tmp
git clone --no-local /path/to/llms-explorer scrub && cd scrub
```

## 5. Build the replacements file

`filter-repo --replace-text` takes `literal==>replacement` lines. Generate it from the
denylist so the terms are never typed into a tracked file:

```bash
python3 - <<'PY' > /tmp/replacements.txt
import re
for line in open("/path/to/llms-explorer/.privacy-denylist"):
    t = line.strip()
    if not t or t.startswith("#"):
        continue
    slug = re.sub(r"[^A-Za-z0-9]+", "-", t).strip("-").upper()[:24] or "TERM"
    print(f"{t}==><REDACTED-{slug}>")
PY

wc -l /tmp/replacements.txt
```

The denylist covers names. For the structural values — operator paths, drive mounts, case
numbers — derive the patterns from the gate rather than restating them here, so there is
one definition and this runbook cannot drift from the detector:

```bash
cd /path/to/llms-explorer
python3 - <<'PY' >> /tmp/replacements.txt
import importlib.util
spec = importlib.util.spec_from_file_location("gate", "scripts/check_publish_privacy.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)          # module is import-safe; main() is __main__-guarded

# Which structural rules to substitute, and what to put in their place. Rules not
# listed here are detection-only — a Slack channel id or a 24-hex object id is better
# reviewed by hand than blanket-replaced.
WANT = {
    "operator home path":  "<ENGAGEMENT_ROOT>",
    "cloud-drive mount":   "<DRIVE_MOUNT>",
    "email inside a path": "<DRIVE_MOUNT>",
    "support case number": "<CASE-NUMBER>",
}
for name, pattern, _why in gate.RULES:
    if name in WANT:
        print(f"regex:{pattern}==>{WANT[name]}")
PY

wc -l /tmp/replacements.txt
```

Read the generated file once before using it. A regex that is right for *detection* can be
too greedy for *substitution* — `filter-repo` will happily rewrite more than you meant.

`/tmp/replacements.txt` contains the very strings you are scrubbing. It must never be
committed, and step 9 deletes it.

## 6. Rewrite — irreversible

```bash
cd /tmp/scrub
git filter-repo --replace-text /tmp/replacements.txt
```

Every commit that contained a term is rewritten and every SHA from that point changes.

## 7. Verify before pushing

Do not skip this. Check the terms are gone from **all** history, not just `HEAD`:

```bash
cd /tmp/scrub
while IFS= read -r term; do
  [ -z "$term" ] && continue
  case "$term" in \#*) continue ;; esac
  n=$(git log --all --oneline -S"$term" | wc -l | tr -d ' ')
  [ "$n" != "0" ] && printf 'STILL PRESENT: %s (%s commits)\n' "$term" "$n"
done < /path/to/llms-explorer/.privacy-denylist
echo "scan complete"

# and the structural gate over the rewritten tree
python3 scripts/check_publish_privacy.py
```

Also confirm you have not lost anything: compare commit counts and check the tree still
builds.

```bash
git rev-list --count --all
cd site && npm ci && npm run build
```

## 8. Force-push, then the part people forget

```bash
cd /tmp/scrub
git push --force --all origin
git push --force --tags origin
```

Then, and this is the step that actually reduces exposure:

- **Ask GitHub Support to purge cached views.** Rewritten commits stay reachable through
  the API and the web UI by SHA until GitHub garbage-collects them. Open a support ticket
  referencing the repository and ask for stale object cleanup. Without this, the old
  content is still fetchable by anyone who knows a SHA.
- **Close and recreate any open PR.** Their SHAs no longer exist.
- **Delete and recreate forks**, or ask fork owners to. A fork keeps its own copy and a
  rewrite of the upstream does not touch it.
- **Everyone re-clones.** A `git pull` into an old clone reintroduces the old objects:

  ```bash
  mv llms-explorer llms-explorer-old && git clone <url> llms-explorer
  ```

- **Rotate anything that was a credential.** Nothing in this particular incident was a
  secret, but if a future scrub covers a token, the rewrite does not make it safe — only
  rotation does.

## 9. Clean up

```bash
rm -f /tmp/replacements.txt
rm -rf /tmp/scrub
```

Keep the bundle from step 2 somewhere private until you are satisfied.

## What this does not fix

The identifiers were in this repository for a period during which it was public. Anyone
who cloned, forked, or read it in that window still has them, and no rewrite reaches
those copies. If that matters for the material in question, the disclosure conversation is
the real remediation and this runbook is only hygiene.
