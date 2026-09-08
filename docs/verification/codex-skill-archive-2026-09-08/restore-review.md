# Restore helper review

Scope: scripts/restore_archived_codex_skills.py. Profile: small. Python CLI plus code-reviewer/coding-standards reference guidance. Structural review; no held-out benchmark exists for empirical optimization.

Convergence and severity contract: /Users/mitch/.claude/skill-consolidation/convergence-and-severity.md.

Iteration 1: Critical 0, High 1, Medium 1, Low 0, Nit 0.
Iteration 2: Critical 0, High 0, Medium 0, Low 0, Nit 0.

- P2/C3 High: shutil.copy2 after preflight could overwrite a file created by sync between checks. Fixed with staged file and exclusive hard-link publication; reject noncanonical targets and changed existing content.
- S5 Medium: partial restore progress was not logged before later RPC failure. Added per-entry completion output so interrupted runs identify completed work.

All C1-C3, S1-S5, P1-P2, M1-M2, M4, T1-T3 reviewed. M3 and T4 are not applicable to this single non-test CLI. Parallel review workers could not open files due to host error `Too many open files (os error 24)`; no results were treated as passes. Closing workers recovered execution. Local review supplied findings. A separate fresh-context final reviewer received only code and pass list and returned zero corroborated Medium+ findings.

Verification: py_compile passed before and after changes. Real archive preflight passed for 64 files. Isolated temporary fixtures verified dry-run makes no changes, mocked-RPC restore, repeat restore, refusal to overwrite changed files, and refusal of mismatched archive hashes. The live archive was not restored. Actual Codex disable RPC and loader were verified separately during curation.

Status: CLEAN. Two local iterations; final blind review passed.

Snapshot and rollback:

```sh
cp /Users/mitch/.claude/skill-consolidation/backups/restore-skills-20260908/restore_archived_codex_skills.py.iter1 scripts/restore_archived_codex_skills.py
```
