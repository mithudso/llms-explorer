"""Parsed routing identifiers must survive the YAML representation intact."""
import os
from pathlib import Path
import re

import pytest
import yaml

SKILLS = next(p for p in Path(__file__).resolve().parents
              if p.name == "skills" and (p / "artifact-to-procedure/SKILL.md").is_file())
SOURCE = Path(os.environ.get("SKO_TEST_SKILLS_ROOT", SKILLS))
NAMES = ["artifact-to-procedure", "crawl-customer-to-llms", "crawl-repo-to-llms",
         "crawl-to-llms-txt", "llms-concept-abstractor", "llms-deep-optimizer",
         "memory-to-llms-txt", "note-organizer", "notes-to-llms", "notes-to-llms-txt",
         "skill-tree-architect"]


@pytest.mark.parametrize("name", NAMES)
def test_folded_description_preserves_complete_tokens(name):
    description = yaml.safe_load((SOURCE / name / "SKILL.md").read_text().split("---", 2)[1])["description"]
    assert not re.search(r"[\w/][\w/-]*-\s+[a-z][\w-]*(?:\.[a-z]+)?", description), description
    assert len(description) <= 1000


@pytest.mark.parametrize("name,token", [
    ("crawl-repo-to-llms", "/crawl-repo2llms"),
    ("memory-to-llms-txt", "notes-to-llms-txt"),
    ("note-organizer", "content-ingestion-extraction"),
    ("notes-to-llms", "references/document-distiller.md"),
])
def test_concrete_alias_and_deferral_tokens(name, token):
    description = yaml.safe_load((SOURCE / name / "SKILL.md").read_text().split("---", 2)[1])["description"]
    assert token in description
