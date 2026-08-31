# ruff: noqa: E501  -- fixture strings and asserted spans are real site lines; wrapping changes what is tested
"""Task 8 — the GitHub Actions workflow builds the site, runs the tests and
gates on the llms lint; the link check runs on main only."""
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/site.yml"


def _run_steps(wf: dict) -> str:
    return " ".join(s.get("run", "") for j in wf["jobs"].values() for s in j["steps"])


def test_workflow_runs_build_tests_and_lint_gate():
    wf = yaml.safe_load(WORKFLOW.read_text())
    steps = _run_steps(wf)
    assert "sh hub/bootstrap.sh" in steps and "npm run build" in steps
    assert "pytest site/tests" in steps
    assert "llms_lint.py check site/dist/llms.txt" in steps and "--json" in steps
    assert "--check-links" in steps and "refs/heads/main" in WORKFLOW.read_text()


def test_workflow_lints_every_family_member_and_uploads_dist():
    wf = yaml.safe_load(WORKFLOW.read_text())
    steps = _run_steps(wf)
    for member in ("llms.txt", "llms-full.txt", "llms-small.txt", "llms-facts.txt", "llms-vocabulary.txt"):
        assert f"site/dist/{member}" in steps, member
    uses = [s.get("uses", "") for j in wf["jobs"].values() for s in j["steps"]]
    assert any(u.startswith("actions/upload-artifact@") for u in uses)
    assert any(u.startswith("actions/setup-node@") for u in uses)
    assert any(u.startswith("actions/setup-python@") for u in uses)


def test_link_check_step_is_gated_to_main():
    wf = yaml.safe_load(WORKFLOW.read_text())
    link_steps = [s for j in wf["jobs"].values() for s in j["steps"] if "--check-links" in s.get("run", "")]
    assert link_steps, "no --check-links step"
    for s in link_steps:
        assert "refs/heads/main" in str(s.get("if", "")), "link check must run only on main"


def test_readme_documents_pages_settings():
    readme = (ROOT / "site/README.md").read_text()
    for needle in ("sh hub/bootstrap.sh", "npm run build", "SITE_URL", "llms.overrides.json", "outputs/"):
        assert needle in readme, needle


def test_refresh_pushes_snapshot_and_ci_promotes():
    """Task 9 — the daily refresh lands on `snapshot`; CI fast-forwards `main`
    only after the build + lint job is green (master §8)."""
    sh = (ROOT / "scripts/refresh_snapshot.sh").read_text()
    assert "git push -q origin HEAD:snapshot" in sh and "HEAD:main" not in sh
    wf = yaml.safe_load(WORKFLOW.read_text())
    promote = wf["jobs"]["promote"]
    assert promote["needs"] == "build" and "refs/heads/snapshot" in promote["if"]


def test_promote_job_fast_forwards_main_with_full_history():
    wf = yaml.safe_load(WORKFLOW.read_text())
    promote = wf["jobs"]["promote"]
    assert "success()" in promote["if"]
    checkouts = [s for s in promote["steps"] if s.get("uses", "").startswith("actions/checkout@")]
    assert checkouts and checkouts[0]["with"]["fetch-depth"] == 0, "promote needs full history to fast-forward"
    runs = " ".join(s.get("run", "") for s in promote["steps"])
    assert "git push origin HEAD:main" in runs
    assert promote.get("permissions", {}).get("contents") == "write"


def test_bootstrap_runs_only_the_hub_tests_the_site_depends_on():
    """`sh hub/bootstrap.sh` is the first CI step, so it must not fail on hub
    subsystems the site never loads: it installs requirements-dev.txt (which
    carries mcp + pyyaml) and runs the llms_lint / docset_refine tests only.
    The whole vendored suite stays one flag away."""
    sh = (ROOT / "hub/bootstrap.sh").read_text()
    assert "-r requirements-dev.txt" in sh
    assert "tests/test_llms_lint.py" in sh and "tests/test_docset_refine.py" in sh
    assert "--all-tests" in sh and "--no-tests" in sh
    # the whole tests/ tree is reachable only through the --all-tests branch
    whole_suite = [ln.strip() for ln in sh.splitlines() if ln.strip() == "set -- tests/"]
    assert len(whole_suite) == 1, "the default run must not hand all of tests/ to pytest"
    all_branch = sh.split('elif [ "$MODE" = all ]', 1)
    assert len(all_branch) == 2 and "set -- tests/\n" in all_branch[1].split("else", 1)[0]


def test_ci_installs_python_deps_only_through_bootstrap():
    """No ad-hoc `pip install` steps: every dependency the workflow needs comes
    from hub/requirements-dev.txt, so CI and a local bootstrap agree."""
    wf = yaml.safe_load(WORKFLOW.read_text())
    for job in wf["jobs"].values():
        for step in job["steps"]:
            run = step.get("run", "")
            assert "pip install" not in run, f"ad-hoc pip install in step {step.get('name')!r}"
    assert "pyyaml" in (ROOT / "hub/requirements-dev.txt").read_text()


def test_link_check_is_advisory_on_push_and_blocking_on_schedule():
    """Cloudflare Pages deploys the same commit that triggers the push run, so
    HEAD-checking the live site cannot gate a push; the daily schedule and a
    manual dispatch check it for real."""
    wf = yaml.safe_load(WORKFLOW.read_text())
    on = wf[True] if True in wf else wf["on"]          # yaml parses bare `on:` as True
    assert "schedule" in on and "workflow_dispatch" in on
    link_steps = [s for j in wf["jobs"].values() for s in j["steps"] if "--check-links" in s.get("run", "")]
    assert link_steps
    for s in link_steps:
        coe = str(s.get("continue-on-error", ""))
        assert "github.event_name == 'push'" in coe, "link check must not gate a push"


def test_readme_documents_a_working_pages_build_command_and_promote_token():
    readme = (ROOT / "site/README.md").read_text()
    build_row = next(ln for ln in readme.splitlines() if ln.startswith("| Build command"))
    assert "hub/bootstrap.sh" in build_row, "bare `npm run build` has no hub/.venv for postbuild"
    assert "PROMOTE_TOKEN" in readme and "contents:write" in readme
    assert "Task 9" not in readme, "promotion ships in this workflow; describe the promote job"


def test_ci_checks_the_generated_data_is_current():
    """Task 8 — `src/data/*.json` is generated and committed, so CI regenerates
    what it can run anywhere (the tree) and diffs it against the committed copy:
    a stale file fails the build, which is what keeps "generated, never
    hand-edited" true."""
    wf = WORKFLOW.read_text()
    assert "gen_tree.py" in wf and "--out" in wf
    assert "diff" in wf or "cmp" in wf


def test_generate_script_runs_the_generators_that_run_anywhere():
    """`npm run generate` is the one command that refreshes the committed data.
    `gen_demo.py` is excluded: it queries the live hub's indexes, so it is run
    by hand on the M5 and its output committed."""
    pkg = json.loads((ROOT / "site/package.json").read_text())
    gen = pkg["scripts"]["generate"]
    for tool in ("gen_reference.py", "gen_tree.py", "gen_directory.py"):
        assert tool in gen, tool
    assert "gen_demo.py" not in gen
    assert "generate" not in pkg["scripts"]["build"], "a build must not regenerate committed data"


def test_readme_documents_the_step2_tools():
    r = (ROOT / "site/README.md").read_text()
    for t in ("gen_tree.py", "gen_directory.py", "gen_demo.py"):
        assert t in r, t
    low = r.lower()
    assert "run by hand on the m5" in low or "needs the live hub" in low
