# llmsx/tests/test_skills.py
"""Offline: every client here is a fake. Nothing in this file opens a socket."""
import pytest

from llmsx import skills

FOLDED = """---
name: demo-skill
description: >-
  Turn a mess into a shape. TRIGGER: /demo, "do the demo thing".
  SKIP: something else entirely → other-skill.
version: "1.2.0"
model: claude-sonnet-5
effort: medium
tags: [llms, demo]
related_skills:
  - other-skill
  - third-skill
metadata:
  changelog: |
    2026-09-01 v1.2.0 — a nested block: with a colon in it
---
# Demo Skill

Body line one.

## Step 1

Do the thing.
"""


def _write_skill(root, name, text=FOLDED):
    directory = root / name
    (directory / "references").mkdir(parents=True)
    (directory / "SKILL.md").write_text(text, encoding="utf-8")
    return directory


# --- parsing ----------------------------------------------------------- #

def test_frontmatter_folds_scalars_and_keeps_the_body(tmp_path):
    _write_skill(tmp_path, "demo-skill")
    skill = skills.load_skill("demo-skill", search_paths=[tmp_path])

    assert skill.name == "demo-skill"
    assert skill.model == "claude-sonnet-5"
    assert skill.effort == "medium"
    # folded scalar: the two source lines become one line, not a literal newline
    assert "TRIGGER: /demo" in skill.description
    assert "\n" not in skill.description
    assert skill.frontmatter["related_skills"] == ["other-skill", "third-skill"]
    assert skill.frontmatter["tags"] == ["llms", "demo"]
    assert skill.body.lstrip().startswith("# Demo Skill")


def test_subset_parser_matches_on_the_fields_the_sdk_reads(tmp_path):
    """The fallback runs when PyYAML is absent; assert it directly either way."""
    source, _body = skills._split_frontmatter(FOLDED)
    parsed = skills._parse_frontmatter_subset(source)

    assert parsed["name"] == "demo-skill"
    assert parsed["version"] == "1.2.0"          # quotes stripped
    assert parsed["tags"] == ["llms", "demo"]
    assert parsed["related_skills"] == ["other-skill", "third-skill"]
    assert "TRIGGER: /demo" in parsed["description"]
    # a nested mapping is kept, not mangled, and its colon survives
    assert "with a colon in it" in parsed["metadata"]["changelog"]


def test_description_first_frontmatter_parses(tmp_path):
    """Real skills put `description` first as often as `name`; both must work."""
    text = FOLDED.replace("name: demo-skill\n", "") .replace(
        'version: "1.2.0"', 'name: desc-first\nversion: "1.2.0"')
    _write_skill(tmp_path, "desc-first", text)
    skill = skills.load_skill("desc-first", search_paths=[tmp_path])
    assert skill.name == "desc-first"
    assert skill.description.startswith("Turn a mess into a shape.")


def test_a_file_without_frontmatter_is_a_parse_error(tmp_path):
    directory = tmp_path / "bare"
    directory.mkdir()
    (directory / "SKILL.md").write_text("# no frontmatter here", encoding="utf-8")
    with pytest.raises(skills.SkillParseError):
        skills.load_skill("bare", search_paths=[tmp_path])


def test_unclosed_frontmatter_is_a_parse_error(tmp_path):
    directory = tmp_path / "unclosed"
    directory.mkdir()
    (directory / "SKILL.md").write_text("---\nname: x\nbody with no fence\n", encoding="utf-8")
    with pytest.raises(skills.SkillParseError):
        skills.load_skill("unclosed", search_paths=[tmp_path])


# --- loading ----------------------------------------------------------- #

def test_missing_skill_raises_with_the_paths_tried(tmp_path):
    with pytest.raises(skills.SkillNotFoundError) as excinfo:
        skills.load_skill("nope", search_paths=[tmp_path])
    message = str(excinfo.value)
    assert "nope" in message
    assert str(tmp_path) in message              # the fix is in the message
    assert excinfo.value.tried                   # and machine-readable too


def test_search_path_order_is_first_hit_wins(tmp_path):
    first, second = tmp_path / "a", tmp_path / "b"
    _write_skill(first, "dupe", FOLDED.replace("model: claude-sonnet-5", "model: from-first"))
    _write_skill(second, "dupe", FOLDED.replace("model: claude-sonnet-5", "model: from-second"))
    assert skills.load_skill("dupe", search_paths=[first, second]).model == "from-first"
    assert skills.load_skill("dupe", search_paths=[second, first]).model == "from-second"


def test_available_skills_lists_and_dedupes(tmp_path):
    first, second = tmp_path / "a", tmp_path / "b"
    _write_skill(first, "one")
    _write_skill(first, "two")
    _write_skill(second, "two")
    _write_skill(second, "three")
    # sorted within a directory, directories in search order — so `three` from
    # the second directory lands after both of the first's, and `two` is not
    # repeated when the second directory also has it.
    assert skills.available_skills(search_paths=[first, second]) == ["one", "two", "three"]


def test_env_var_extends_the_search_path(tmp_path, monkeypatch):
    _write_skill(tmp_path, "env-skill")
    monkeypatch.setenv("LLMSX_SKILL_PATH", str(tmp_path))
    assert skills.skill_search_paths()[0] == tmp_path
    assert skills.load_skill("env-skill").name == "demo-skill"   # frontmatter name wins


# --- prompt assembly --------------------------------------------------- #

def test_system_prompt_carries_the_body_verbatim(tmp_path):
    _write_skill(tmp_path, "demo-skill")
    skill = skills.load_skill("demo-skill", search_paths=[tmp_path])
    prompt = skill.system_prompt()
    assert "Do the thing." in prompt
    assert "demo-skill" in prompt
    assert "reference:" not in prompt            # not requested, not included


def test_references_are_included_only_on_request(tmp_path):
    directory = _write_skill(tmp_path, "demo-skill")
    (directory / "references" / "loop.md").write_text("The loop rule.", encoding="utf-8")
    skill = skills.load_skill("demo-skill", search_paths=[tmp_path])

    assert [p.name for p in skill.reference_files()] == ["loop.md"]
    assert "The loop rule." not in skill.system_prompt()
    assert "The loop rule." in skill.system_prompt(include_references=True)


# --- running ----------------------------------------------------------- #

class FakeMessages:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


class FakeClient:
    def __init__(self, response):
        self.messages = FakeMessages(response)


class FakeBlock:
    def __init__(self, text):
        self.text = text


class FakeResponse:
    def __init__(self, text):
        self.content = [FakeBlock(text)]
        self.stop_reason = "end_turn"
        self.usage = {"input_tokens": 11, "output_tokens": 7}


def test_run_skill_sends_the_skill_as_system_and_returns_the_text(tmp_path):
    _write_skill(tmp_path, "demo-skill")
    skill = skills.load_skill("demo-skill", search_paths=[tmp_path])
    client = FakeClient(FakeResponse("the answer"))

    run = skills.run_skill(skill, "my messy notes", client=client)

    assert run.text == "the answer"
    assert run.skill == "demo-skill"
    assert run.model == "claude-sonnet-5"        # from the skill's frontmatter
    assert run.stop_reason == "end_turn"
    assert run.usage == {"input_tokens": 11, "output_tokens": 7}

    sent = client.messages.calls[0]
    assert "Do the thing." in sent["system"]
    assert sent["messages"] == [{"role": "user", "content": "my messy notes"}]
    assert sent["max_tokens"] == skills.DEFAULT_MAX_TOKENS


def test_caller_model_overrides_the_frontmatter(tmp_path):
    _write_skill(tmp_path, "demo-skill")
    client = FakeClient(FakeResponse("ok"))
    run = skills.run_skill(
        skills.load_skill("demo-skill", search_paths=[tmp_path]),
        "input", client=client, model="claude-opus-5", max_tokens=99)
    assert run.model == "claude-opus-5"
    assert client.messages.calls[0]["max_tokens"] == 99


def test_a_plain_callable_is_a_valid_client(tmp_path):
    _write_skill(tmp_path, "demo-skill")
    seen = {}

    def fake(**kwargs):
        seen.update(kwargs)
        return "plain string reply"

    run = skills.run_skill(
        skills.load_skill("demo-skill", search_paths=[tmp_path]), "input", client=fake)

    assert run.text == "plain string reply"
    assert seen["messages"][0]["content"] == "input"


def test_dict_shaped_response_is_understood(tmp_path):
    _write_skill(tmp_path, "demo-skill")
    client = FakeClient({"content": [{"type": "text", "text": "dict reply"}],
                         "stop_reason": "end_turn", "usage": {"output_tokens": 3}})
    run = skills.run_skill(skills.load_skill("demo-skill", search_paths=[tmp_path]),
                           "input", client=client)
    assert run.text == "dict reply"
    assert run.usage == {"output_tokens": 3}


def test_empty_task_input_is_refused_before_any_call(tmp_path):
    _write_skill(tmp_path, "demo-skill")
    skill = skills.load_skill("demo-skill", search_paths=[tmp_path])
    client = FakeClient(FakeResponse("never sent"))
    with pytest.raises(ValueError):
        skills.run_skill(skill, "   ", client=client)
    assert client.messages.calls == []


def test_run_skill_accepts_a_name_and_loads_it(tmp_path, monkeypatch):
    _write_skill(tmp_path, "demo-skill")
    monkeypatch.setenv("LLMSX_SKILL_PATH", str(tmp_path))
    run = skills.run_skill("demo-skill", "input", client=FakeClient(FakeResponse("named")))
    assert run.text == "named"


def test_extra_system_is_appended_after_the_skill(tmp_path):
    _write_skill(tmp_path, "demo-skill")
    client = FakeClient(FakeResponse("ok"))
    skills.run_skill(skills.load_skill("demo-skill", search_paths=[tmp_path]),
                     "input", client=client, extra_system="Answer in JSON.")
    system = client.messages.calls[0]["system"]
    assert system.rstrip().endswith("Answer in JSON.")


# --- CLI: family / optimize -------------------------------------------- #
# These skills orchestrate multi-pass loops and subagents on the real Claude
# Code install; here they are just names `run_skill` loads a SKILL.md for,
# so the fixture skill stands in and `skills._default_client` is patched to
# a fake — no test in this file opens a socket.

def test_cli_family_prints_the_disclaimer_then_the_skill_output(tmp_path, monkeypatch, capsys):
    from llmsx.__main__ import main

    _write_skill(tmp_path, "concept-family-explorer",
                FOLDED.replace("name: demo-skill", "name: concept-family-explorer"))
    monkeypatch.setenv("LLMSX_SKILL_PATH", str(tmp_path))
    monkeypatch.setattr(skills, "_default_client",
                        lambda: FakeClient(FakeResponse("mapped the family")))

    assert main(["family", "http caching"]) == 0
    out, err = capsys.readouterr()
    assert "single model turn" in err
    assert "concept-family-explorer" in err
    assert "not the full" in err
    assert "mapped the family" in out


def test_cli_optimize_reads_a_file_and_runs_llms_deep_optimizer(tmp_path, monkeypatch, capsys):
    from llmsx.__main__ import main

    _write_skill(tmp_path, "llms-deep-optimizer",
                FOLDED.replace("name: demo-skill", "name: llms-deep-optimizer"))
    monkeypatch.setenv("LLMSX_SKILL_PATH", str(tmp_path))
    monkeypatch.setattr(skills, "_default_client",
                        lambda: FakeClient(FakeResponse("optimized")))
    target = tmp_path / "llms.txt"
    target.write_text("# stuff\n", encoding="utf-8")

    assert main(["optimize", str(target)]) == 0
    out, err = capsys.readouterr()
    assert "single model turn" in err
    assert "llms-deep-optimizer" in err
    assert "optimized" in out


def test_cli_optimize_accepts_raw_text_when_target_is_not_a_file(tmp_path, monkeypatch, capsys):
    from llmsx.__main__ import main

    _write_skill(tmp_path, "llms-deep-optimizer",
                FOLDED.replace("name: demo-skill", "name: llms-deep-optimizer"))
    monkeypatch.setenv("LLMSX_SKILL_PATH", str(tmp_path))
    seen = {}

    def fake(**kwargs):
        seen.update(kwargs)
        return "ok"

    monkeypatch.setattr(skills, "_default_client", lambda: fake)
    assert main(["optimize", "not a real path, just text"]) == 0
    assert seen["messages"][0]["content"] == "not a real path, just text"


def test_cli_optimize_refuses_a_file_over_the_size_cap(tmp_path, monkeypatch, capsys):
    from llmsx.__main__ import main

    _write_skill(tmp_path, "llms-deep-optimizer",
                FOLDED.replace("name: demo-skill", "name: llms-deep-optimizer"))
    monkeypatch.setenv("LLMSX_SKILL_PATH", str(tmp_path))
    big = tmp_path / "huge.txt"
    big.write_bytes(b"x" * (1_000_001))

    code = main(["optimize", str(big)])
    assert code == 2
    assert "over the" in capsys.readouterr().err


def test_cli_family_without_the_skills_extra_is_a_clean_error_not_a_traceback(
        tmp_path, monkeypatch, capsys):
    from llmsx.__main__ import main

    _write_skill(tmp_path, "concept-family-explorer",
                FOLDED.replace("name: demo-skill", "name: concept-family-explorer"))
    monkeypatch.setenv("LLMSX_SKILL_PATH", str(tmp_path))

    def boom():
        raise RuntimeError(
            "no client passed and the `anthropic` package is not installed")
    monkeypatch.setattr(skills, "_default_client", boom)

    assert main(["family", "http caching"]) == 2
    assert "anthropic" in capsys.readouterr().err


# --- the real skills on disk ------------------------------------------- #

# --- name validation: a skill name is not a path ------------------------- #

def test_load_skill_rejects_a_path_traversal_name(tmp_path):
    for bad in ("../elsewhere", "/abs/path", "..", ""):
        with pytest.raises(skills.SkillNotFoundError):
            skills.load_skill(bad, search_paths=[tmp_path])


def test_load_skill_still_accepts_a_leading_underscore_name(tmp_path):
    _write_skill(tmp_path, "_private-skill")
    skill = skills.load_skill("_private-skill", search_paths=[tmp_path])
    assert skill.name == "demo-skill"      # frontmatter name wins, as elsewhere


# --- empty frontmatter is valid, not a parse error ------------------------ #

def test_empty_frontmatter_parses_to_an_empty_mapping():
    fm, body = skills._split_frontmatter("---\n---\njust a body\n")
    assert fm == ""
    assert body == "just a body\n"


def test_a_skill_with_empty_frontmatter_loads(tmp_path):
    directory = tmp_path / "bare-front"
    directory.mkdir()
    (directory / "SKILL.md").write_text("---\n---\n# Body only\n", encoding="utf-8")
    skill = skills.load_skill("bare-front", search_paths=[tmp_path])
    assert skill.body.strip().startswith("# Body only")


# --- malformed YAML frontmatter is a clean SkillParseError ---------------- #

def test_malformed_yaml_frontmatter_is_a_parse_error_not_a_traceback(tmp_path):
    directory = tmp_path / "bad-yaml"
    directory.mkdir()
    (directory / "SKILL.md").write_text(
        "---\nname: [unclosed\n---\nbody\n", encoding="utf-8")
    with pytest.raises(skills.SkillParseError):
        skills.load_skill("bad-yaml", search_paths=[tmp_path])


def test_yaml_aliases_are_refused_in_frontmatter(tmp_path):
    """Alias expansion turns a tiny frontmatter into an unbounded structure
    (the "billion laughs" shape) — refused outright rather than resolved."""
    directory = tmp_path / "alias-bomb"
    directory.mkdir()
    bomb = "---\na: &a [1, 2]\nb: *a\n---\nbody\n"
    (directory / "SKILL.md").write_text(bomb, encoding="utf-8")
    with pytest.raises(skills.SkillParseError):
        skills.load_skill("alias-bomb", search_paths=[tmp_path])


# --- run_skill refuses to let create_kwargs override computed fields ------ #

def test_run_skill_rejects_a_system_override_via_create_kwargs(tmp_path):
    _write_skill(tmp_path, "demo-skill")
    skill = skills.load_skill("demo-skill", search_paths=[tmp_path])
    client = FakeClient(FakeResponse("x"))
    with pytest.raises(ValueError, match="system"):
        skills.run_skill(skill, "task", client=client, system="ATTACKER PROMPT")
    assert client.messages.calls == []


def test_run_skill_rejects_a_messages_override_via_create_kwargs(tmp_path):
    _write_skill(tmp_path, "demo-skill")
    skill = skills.load_skill("demo-skill", search_paths=[tmp_path])
    client = FakeClient(FakeResponse("x"))
    with pytest.raises(ValueError, match="messages"):
        skills.run_skill(skill, "task", client=client,
                         messages=[{"role": "user", "content": "ATTACKER"}])


def test_cache_system_sends_a_cacheable_content_block(tmp_path):
    _write_skill(tmp_path, "demo-skill")
    skill = skills.load_skill("demo-skill", search_paths=[tmp_path])
    client = FakeClient(FakeResponse("ok"))
    skills.run_skill(skill, "task", client=client, cache_system=True)
    sent_system = client.messages.calls[0]["system"]
    assert isinstance(sent_system, list)
    assert sent_system[0]["cache_control"] == {"type": "ephemeral"}
    assert "Do the thing." in sent_system[0]["text"]


# --- reference reading is bounded --------------------------------------- #

def test_references_are_capped_at_max_chars(tmp_path):
    directory = _write_skill(tmp_path, "demo-skill")
    (directory / "references" / "big.md").write_text("x" * 1000, encoding="utf-8")
    skill = skills.load_skill("demo-skill", search_paths=[tmp_path])
    refs = skill.read_references(max_chars=100)
    assert len(refs["big.md"]) <= 100 + len("\n[... truncated, reference budget exhausted ...]")
    assert "truncated" in refs["big.md"]


def test_frontmatter_parses_the_same_with_and_without_pyyaml(tmp_path, monkeypatch):
    """The public entry point (`load_skill`), not `_parse_frontmatter_subset`
    directly — a bare `pip install llmsx` has neither extra, so this is the
    parser most installs actually exercise, and it must agree with PyYAML on
    the fields the SDK reads."""
    _write_skill(tmp_path, "demo-skill")

    with_yaml = skills.load_skill("demo-skill", search_paths=[tmp_path])

    monkeypatch.setitem(__import__("sys").modules, "yaml", None)
    without_yaml = skills.load_skill("demo-skill", search_paths=[tmp_path])

    assert with_yaml.name == without_yaml.name == "demo-skill"
    assert with_yaml.model == without_yaml.model == "claude-sonnet-5"
    assert with_yaml.effort == without_yaml.effort == "medium"
    assert with_yaml.frontmatter["tags"] == without_yaml.frontmatter["tags"] == ["llms", "demo"]


def test_reference_files_rejects_a_symlink_escape(tmp_path):
    directory = _write_skill(tmp_path, "demo-skill")
    outside = tmp_path / "secret.md"
    outside.write_text("LEAKED REFERENCE CONTENT", encoding="utf-8")
    (directory / "references" / "trap.md").symlink_to(outside)
    skill = skills.load_skill("demo-skill", search_paths=[tmp_path])
    assert skill.reference_files() == []
    assert skill.read_references() == {}


def test_the_repo_skills_parse(tmp_path):
    """The eight skills this SDK exists to run must actually load.

    Skipped rather than failed when the checkout has no `skills/` dir: the
    package installs standalone and its tests must pass there too.
    """
    repo_skills = skills.SKILLS_REL
    from pathlib import Path
    root = Path(__file__).resolve().parents[2] / repo_skills
    if not root.is_dir():
        pytest.skip("no repo skills/ directory in this checkout")
    names = skills.available_skills(search_paths=[root])
    assert names, "expected at least one skill in the repo"
    for name in names:
        skill = skills.load_skill(name, search_paths=[root])
        assert skill.description, f"{name} has no description"
        assert skill.body.strip(), f"{name} has an empty body"
