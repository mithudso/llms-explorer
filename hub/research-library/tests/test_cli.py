import io
import json

from research_library_service import cli
from research_library_service.service import Service


class ServiceFixture:
    def __init__(self):
        self.calls = []

    def dispatch(self, operation, arguments, **context):
        self.calls.append((operation, arguments, context))
        return {"operation": operation, "accepted": True}


def test_json_request_keeps_local_role_and_legacy_owner(capsys):
    service = ServiceFixture()
    request = {"operation": "lease_acquire", "arguments": {
        "concept_ids": ["c:example"], "owner": "legacy:owned-run",
    }}
    assert cli.main(["request"], service=service,
                    input_stream=io.StringIO(json.dumps(request))) == 0
    assert json.loads(capsys.readouterr().out)["accepted"]
    assert service.calls[0][2] == {"role": "admin", "actor": "local-admin"}
    assert service.calls[0][1]["owner"] == "legacy:owned-run"


def test_named_request_arguments_and_rejected_envelope_elevation(capsys):
    service = ServiceFixture()
    assert cli.main(["--role", "read", "request", "concept_get"], service=service,
                    input_stream=io.StringIO('{"concept_id":"c:x"}')) == 0
    assert service.calls[0] == ("concept_get", {"concept_id": "c:x"},
                                 {"role": "read", "actor": "local-read"})
    capsys.readouterr()
    assert cli.main(["request"], service=service, input_stream=io.StringIO(
        '{"operation":"status","role":"admin","arguments":{}}')) == 2
    assert len(service.calls) == 1


def test_cli_errors_never_print_driver_credentials(capsys):
    class Broken:
        def dispatch(self, *args, **kwargs):
            raise RuntimeError("mongodb://name:very-private-password@private-address/")
    assert cli.main(["status"], service=Broken()) == 2
    captured = capsys.readouterr()
    assert not captured.out and "very-private" not in captured.err
    assert "private-address" not in captured.err
    assert json.loads(captured.err)["error"] == "RuntimeError"


def test_import_denied_to_reader_before_importer_load(capsys):
    service = Service(config={}, bridge={})
    assert cli.main(["--role", "read", "import", "--tree", "/unused/tree.json"],
                    service=service) == 2
    assert service._store is None
    assert json.loads(capsys.readouterr().err)["error"] == "PermissionError"


def test_import_and_search_flags(capsys):
    service = ServiceFixture()
    assert cli.main(["import", "--tree", "/private/tree.json", "--queue", "/private/q.md",
                     "--scores", "/private/scores.json", "--artifact", "/private/artifact.json",
                     "--repo", "/repo", "--dry-run"], service=service) == 0
    operation, args, _ = service.calls[-1]
    assert operation == "import" and args["tree_paths"] == ["/private/tree.json"]
    assert args["dry_run"] and not args["replace_import"]
    assert cli.main(["search", "exact terminology", "--breadth", "narrow",
                     "--topic-id", "c:x", "--mode", "keyword"], service=service) == 0
    assert service.calls[-1][1]["topic_id"] == "c:x"
    capsys.readouterr()


def test_explicit_environment_is_literal_and_preserves_existing(tmp_path, monkeypatch):
    from research_library_service.environment import load_environment
    path = tmp_path / "client.env"
    marker = tmp_path / "never-created"
    literal = chr(36) + "{A_LITERAL}"
    path.write_text(f"A_LITERAL=$(touch {marker})\nB_LITERAL={literal}\nEXISTING=changed\n")
    monkeypatch.setenv("EXISTING", "preserved")
    monkeypatch.delenv("A_LITERAL", raising=False)
    monkeypatch.delenv("B_LITERAL", raising=False)
    load_environment(path)
    import os
    assert os.environ["A_LITERAL"] == f"$(touch {marker})"
    assert os.environ["B_LITERAL"] == literal and os.environ["EXISTING"] == "preserved"
    assert not marker.exists()
    monkeypatch.delenv("A_LITERAL")
    monkeypatch.delenv("B_LITERAL")


def test_environment_does_not_search_cwd(tmp_path, monkeypatch):
    from research_library_service.environment import load_environment
    (tmp_path / ".env").write_text("RESEARCH_UNEXPECTED=should-not-load\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("RESEARCH_LIBRARY_ENV_FILE", raising=False)
    monkeypatch.delenv("RESEARCH_UNEXPECTED", raising=False)
    load_environment()
    import os
    assert "RESEARCH_UNEXPECTED" not in os.environ
