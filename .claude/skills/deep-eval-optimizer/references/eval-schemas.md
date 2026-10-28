# Eval Schemas Reference

## 1. Functional Evals (`evals/evals.json`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "skill_name": "<skill-name>",
  "version": "1.0.0",
  "description": "Evaluation suite description",
  "evals": [
    {
      "id": 1,
      "name": "descriptive-eval-name",
      "prompt": "Realistic user input without leaked skill names or answers",
      "expected_output": "Comprehensive deliverable specification",
      "files": ["inputs/fixture.txt"],
      "assertions": [
        {
          "name": "structural check",
          "check": "output contains valid markdown table with headers",
          "type": "structural"
        },
        {
          "name": "content check",
          "check": "all 5 inputs are referenced without omissions",
          "type": "deterministic"
        }
      ]
    }
  ]
}
```

## 2. Trigger Accuracy Evals (`evals/trigger-eval.json`)

Array of exactly 20 query objects:
- 10 `should_trigger: true` (varied user intents, casual/terse/synonym)
- 10 `should_trigger: false` (near-misses, sister skills, out-of-scope)

```json
[
  {
    "query": "tune this system prompt to stop hallucinations",
    "should_trigger": true
  },
  {
    "query": "debug why this postgres query is running slowly",
    "should_trigger": false
  }
]
```
