# site/tests/test_gen_figures.py
import json, sys
from pathlib import Path
SITE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(SITE / "tools"))
import gen_figures  # noqa: E402

def test_collect_reads_every_export_manifest(tmp_path):
    d = tmp_path / "exports" / "ex.dev.llms"; d.mkdir(parents=True)
    (d / "manifest.json").write_text(json.dumps({
        "pages": 3, "units": 12, "sections": ["a/llms.txt"], "dropped_empty_pages": 1,
        "files": {"llms.txt": {"bytes": 900, "tokens": 225}, "llms-full.txt": {"bytes": 4000, "tokens": 1000},
                  "llms-facts.txt": {"bytes": 2000, "tokens": 500}}}))
    f = gen_figures.collect(tmp_path)
    assert f["ex.dev"] == {"pages": 3, "units": 12, "sections": 1, "index_bytes": 900,
                           "full_tokens": 1000, "facts_tokens": 500, "dropped_empty_pages": 1}

def test_real_outputs_have_the_launch_post_docsets():
    f = gen_figures.collect(SITE.parent / "outputs")
    assert {"developers.cloudflare.com", "developer.paypal.com", "code.claude.com", "docs.langchain.com"} <= set(f)
