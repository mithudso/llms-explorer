#!/usr/bin/env python3
"""
Deep Eval Optimizer: Suite Validator & Analytical Passes Engine.
Audits eval suites across Passes A through L and outputs findings with recommendations.
"""

import sys
import json
from pathlib import Path
import math
from typing import Dict, Any, List

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
    if not path.exists():
        return {"error": f"File {eval_file} not found"}

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    findings = []

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
                "severity": "High" if len(negatives) < 5 else "Medium",
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

        for ev in evals:
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
            if skill_name and skill_name in prompt.lower():
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
            files = ev.get("files", [])
            for fpath in files:
                fp = Path(fpath)
                if not fp.is_absolute():
                    fp = path.parent / fpath
                if fp.exists() and fp.stat().st_size > 50 * 1024:
                    findings.append({
                        "pass": "Pass G",
                        "severity": "Medium",
                        "finding": f"Fixture '{fpath}' in eval #{eid} exceeds 50KB ({fp.stat().st_size // 1024}KB)",
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
