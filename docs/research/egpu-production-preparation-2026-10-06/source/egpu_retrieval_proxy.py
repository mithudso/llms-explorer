#!/usr/bin/env python3
"""New declared labels/windows; unchanged canonical publisher and nonworker gate."""
import importlib.util
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
TYPED=Path('/Users/mitch/.cache/claude-egpu/experiments/qwen35-9b-admission/read-binding-diagnostics-preparation-v100')
sys.path.insert(0,str(TYPED))
from llmsx import retrieval_proxy as canonical_relay
import typed_retrieval_proxy as typed
from focused_windows import candidate_base
from provenance_labels import Labels,Input,Output
from publication_form import extend
from acquisition_view import extend as page_handle_view
from observer_numeric import extend as observer_numeric_view
from citation_diagnostics import extend as citation_diagnostic_engine
import publication_form
from form_diagnostics import extend as form_diagnostic
BASE=Path('/Users/mitch/dev/worktrees/skills-egpu-full-qualification/rtx5080-egpu-harness/scripts/egpu_retrieval_proxy.py')
RetrievalProxy=canonical_relay.RetrievalProxy
EgpuRetrievalProxy=candidate_base(typed.load_reviewed_base())
def main():
    if '--declared-new-interface' in sys.argv:
        typed.PublicationEngine=citation_diagnostic_engine(typed.PublicationEngine)
        publication_form.form=form_diagnostic(publication_form.form,publication_form.Refusal)
        ledger=Path(sys.argv[sys.argv.index('--ledger')+1]);labels=Labels(ledger)
        typed.load_reviewed_base=lambda:EgpuRetrievalProxy
        original_factory=typed.proxy_class
        typed.proxy_class=lambda base:observer_numeric_view(page_handle_view(extend(original_factory(base))))
        original_in,original_out=sys.stdin,sys.stdout
        try:
            sys.stdin=Input(original_in,labels);sys.stdout=Output(original_out,labels)
            return typed.main()
        finally:
            sys.stdin,sys.stdout=original_in,original_out
    spec=importlib.util.spec_from_file_location('frozen_original_gate_relay',BASE)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.main()
if __name__=='__main__':raise SystemExit(main())
