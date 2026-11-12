#!/usr/bin/env python3
"""
Deep Eval Optimizer: Suite Validator & Analytical Passes Engine.
Audits eval suites across Passes A through L and outputs findings with recommendations.
"""

import sys
import json
from pathlib import Path
import math
import re
from typing import Dict, Any

PASSES = {
    "Pass A": "Prompt Realism & Ecological Validity",
    "Pass B": "Discriminative Power & Baseline Contrast",
    "Pass C": "Assertion Objectivity & Verifiability",
    "Pass D": "Near-Miss & False-Positive Coverage",
    "Pass E": "Flakiness & Determinism Hygiene",
    "Pass F": "Leakage & Tautology (Answer Contamination)",
    "Pass G": "Input Fixture Integrity & Isolation",
    "Pass H": "Coverage & Boundary Distribution",
    "Pass I": "Expected Output Precision & Completeness",
    "Pass J": "Cost, Latency & Token Efficiency",
    "Pass K": "Anti-Overfitting & Train/Val Split",
    "Pass L": "Format & Schema Compliance"
}

def validate_suite(eval_file: str) -> Dict[str, Any]:
    path = Path(eval_file).resolve()
    findings = []
    resolved_fixtures = {}

    def add(pass_id, message, severity="High"):
        findings.append({"pass": pass_id, "severity": severity, "finding": message,
                         "recommendation": "Repair the suite or fixture before grading execution."})

    def report():
        return {"file": str(path), "total_findings": len(findings),
                "high_findings": sum(f["severity"] == "High" for f in findings),
                "medium_findings": sum(f["severity"] == "Medium" for f in findings),
                "low_findings": sum(f["severity"] == "Low" for f in findings),
                "findings": findings}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        add("Pass L", f"Unreadable or malformed eval JSON: {exc}")
        return report()
    if not isinstance(data, (dict, list)):
        add("Pass L", "Eval JSON must be a functional-suite object or trigger-query array")
        return report()
    if isinstance(data, list):
        for index, row in enumerate(data):
            if (not isinstance(row, dict) or not isinstance(row.get("query"), str)
                    or not row["query"].strip() or type(row.get("should_trigger")) is not bool):
                add("Pass L", f"Trigger row {index} needs a nonempty query and a Boolean should_trigger")
        if findings:
            return report()
        if len(data) != 20:
            add("Pass L", f"Trigger projection has {len(data)} rows; exactly 20 required")
        if len({row["query"] for row in data}) != len(data):
            add("Pass L", "Trigger queries must be unique")
    else:
        if not isinstance(data.get("skill_name"), str) or not data["skill_name"].strip():
            add("Pass L", "Functional suite needs a nonempty skill_name")
        if not isinstance(data.get("evals"), list):
            add("Pass L", "Functional suite needs an evals array")
            return report()
        ids = set()
        for index, case in enumerate(data["evals"]):
            if not isinstance(case, dict):
                add("Pass L", f"Case {index} must be an object")
                continue
            key = case.get("id")
            if not (type(key) is int or isinstance(key, str) and bool(key.strip())):
                add("Pass L", f"Case {index} needs a string or integer id")
            elif key in ids:
                add("Pass L", f"Duplicate case id {key}")
            else:
                ids.add(key)
            for field in ("name", "prompt", "expected_output"):
                if not isinstance(case.get(field), str) or not case[field].strip():
                    add("Pass L", f"Case {index} needs a nonempty {field}")
            intent = case.get("evaluation_intent", "task")
            if not isinstance(intent, str) or intent not in {"task", "manual-invocation", "routing"}:
                add("Pass L", f"Case {index} has an unsupported evaluation_intent")
            assertions = case.get("assertions")
            if not isinstance(assertions, list) or not assertions:
                add("Pass L", f"Case {index} needs a nonempty assertions array")
            else:
                for assertion in assertions:
                    check = assertion if isinstance(assertion, str) else assertion.get("check") if isinstance(assertion, dict) else None
                    if not isinstance(check, str) or not check.strip():
                        add("Pass L", f"Case {index} contains an invalid assertion")
            files = case.get("files", [])
            if not isinstance(files, list) or any(not isinstance(f, str) or not f for f in files):
                add("Pass L", f"Case {index} files must be an array of nonempty paths")
                continue
            skill_root = path.parent.parent if path.parent.name == "evals" else path.parent
            resolved_fixtures[index] = []
            for fixture in files:
                rel = Path(fixture.replace("<INPUT>/", "inputs/"))
                candidates = [(path.parent / rel).resolve(), (skill_root / rel).resolve()]
                if rel.is_absolute():
                    add("Pass G", f"Fixture '{fixture}' escapes the skill tree")
                else:
                    allowed = [candidate for candidate in candidates if candidate.is_relative_to(skill_root)]
                    resolved = next((candidate for candidate in allowed if candidate.is_file()), None)
                    if resolved is not None:
                        resolved_fixtures[index].append((fixture, resolved))
                    elif len(allowed) != len(candidates):
                        add("Pass G", f"Fixture '{fixture}' escapes the skill tree")
                    else:
                        add("Pass G", f"Fixture '{fixture}' is missing")
        # The analytical checks below assume structurally valid rows.
        if any(f["pass"] == "Pass L" for f in findings):
            return report()

    # Check if trigger-eval list or functional-eval dict
    is_trigger_eval = isinstance(data, list)

    if is_trigger_eval:
        # Validate trigger-evals
        positives = [q for q in data if q.get("should_trigger") is True]
        negatives = [q for q in data if q.get("should_trigger") is False]

        # Pass D: Near-miss & false-positive coverage (Trigger Calibration)
        if len(negatives) < 10:
            findings.append({
                "pass": "Pass D",
                "severity": "High",
                "finding": f"Insufficient negative near-miss queries ({len(negatives)} found, min 10 required for trigger calibration)",
                "recommendation": "Add realistic near-miss queries with contrasting intent (Verb_competing + Noun_shared)."
            })

        if len(positives) < 10:
            findings.append({
                "pass": "Pass H",
                "severity": "High" if len(positives) < 5 else "Medium",
                "finding": f"Insufficient positive queries ({len(positives)} found, min 10 required)",
                "recommendation": "Expand positive queries to cover direct, symptom, terse, and context-rich intents."
            })

        # Pass A: Realism
        robotic = [q["query"] for q in data if any(k in q.get("query", "").lower() for k in ["please run the skill", "test query", "execute skill", "using standard parameters"])]
        if robotic:
            findings.append({
                "pass": "Pass A",
                "severity": "Medium",
                "finding": f"Robotic or synthetic prompt phrasing in {len(robotic)} queries",
                "recommendation": "Rewrite prompts to reflect authentic, natural user phrasing and pain points."
            })

    else:
        # Validate functional evals
        skill_name = data.get("skill_name")
        evals = data.get("evals", [])

        # Pass L: Schema
        if not skill_name:
            findings.append({
                "pass": "Pass L",
                "severity": "High",
                "finding": "Missing top-level 'skill_name' in eval suite",
                "recommendation": "Specify canonical skill name."
            })

        if len(evals) < 2:
            findings.append({
                "pass": "Pass H",
                "severity": "Medium",
                "finding": f"Eval suite has only {len(evals)} test case(s); minimum 2-3 required",
                "recommendation": "Add diverse test cases covering happy path, edge cases, and file transformation."
            })

        for index, ev in enumerate(evals):
            eid = ev.get("id")
            name = ev.get("name", f"eval-{eid}")
            prompt = ev.get("prompt", "")
            expected = ev.get("expected_output", "")
            assertions = ev.get("assertions", [])

            # Pass C: Assertion objectivity & Negative Tripwires
            if not assertions:
                findings.append({
                    "pass": "Pass C",
                    "severity": "High",
                    "finding": f"Eval #{eid} '{name}' has no assertions",
                    "recommendation": "Add at least 2 objectively verifiable assertions (Structural, Schema, Deterministic, Negative Bounds)."
                })
            else:
                for a in assertions:
                    txt = a if isinstance(a, str) else a.get("check", "")
                    if any(vibe in txt.lower() for vibe in ["looks good", "well written", "nice", "appropriate"]):
                        findings.append({
                            "pass": "Pass C",
                            "severity": "Medium",
                            "finding": f"Subjective/vague assertion '{txt}' in eval #{eid}",
                            "recommendation": "Replace with concrete structural, schema, or negative bounds checks."
                        })

            # Pass F: Answer leakage, N-gram priming & Saliency Entropy
            invocation = bool(re.match(
                r"\s*(?:please\s+)?(?:run|invoke|use|call)\s+(?:the\s+)?/?" +
                re.escape(skill_name or "") + r"(?=$|[\s.,:;!?])", prompt, re.I
            ))
            allowed_name = ev.get("evaluation_intent") in {"manual-invocation", "routing"} or invocation
            if skill_name and skill_name.casefold() in prompt.casefold() and not allowed_name:
                findings.append({
                    "pass": "Pass F",
                    "severity": "High" if "run the " + skill_name.lower() in prompt.lower() else "Medium",
                    "finding": f"Prompt in eval #{eid} directly leaks skill name '{skill_name}'",
                    "recommendation": "Apply Natural User Persona Transform: describe user symptoms without naming the skill."
                })

            # Tier-3 Saliency Entropy Audit
            words = prompt.split()
            if len(words) >= 15:
                import collections
                counts = collections.Counter(words)
                total = len(words)
                entropy = -sum((c / total) * math.log(c / total) for c in counts.values())
                max_entropy = math.log(len(counts))
                if max_entropy > 0 and (entropy / max_entropy) < 0.45:
                    findings.append({
                        "pass": "Pass F",
                        "severity": "Medium",
                        "finding": f"Low token entropy in eval #{eid} prompt ({entropy:.2f}/{max_entropy:.2f}), suggesting high token concentration or copy-pasted syntax",
                        "recommendation": "Rewrite prompt with realistic natural user phrasing to ensure high token dispersion."
                    })

            # Pass G: Fixture size and isolation
            for fpath, fp in resolved_fixtures.get(index, []):
                try:
                    size = fp.stat().st_size
                except OSError as exc:
                    add("Pass G", f"Resolved fixture '{fpath}' became unreadable: {exc}")
                    continue
                if size > 50 * 1024:
                    findings.append({
                        "pass": "Pass G",
                        "severity": "Medium",
                        "finding": f"Fixture '{fpath}' in eval #{eid} exceeds 50KB ({size // 1024}KB)",
                        "recommendation": "Minify fixture dataset to minimal reproducible representation under 50KB."
                    })

            # Pass I: Expected output precision
            if not expected or len(expected.split()) < 3:
                findings.append({
                    "pass": "Pass I",
                    "severity": "Medium",
                    "finding": f"Underspecified expected output in eval #{eid}",
                    "recommendation": "Detail the exact required artifact sections, shapes, or behavior."
                })


    return {
        "file": str(path),
        "total_findings": len(findings),
        "high_findings": sum(1 for f in findings if f["severity"] == "High"),
        "medium_findings": sum(1 for f in findings if f["severity"] == "Medium"),
        "low_findings": sum(1 for f in findings if f["severity"] == "Low"),
        "findings": findings
    }

def main():
    if len(sys.argv) < 2:
        print("Usage: python suite_validator.py <path-to-eval-file>")
        sys.exit(1)

    res = validate_suite(sys.argv[1])
    print(json.dumps(res, indent=2))

if __name__ == "__main__":
    main()
