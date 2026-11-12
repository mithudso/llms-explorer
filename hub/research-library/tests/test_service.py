import pytest

from research_library_service.service import Service, public_error, validate_arguments


class Store:
    def __init__(self):
        self.calls = []

    def status(self):
        return {"ready": True}

    def concept_create(self, name, actor="agent", request_id=""):
        self.calls.append((name, actor, request_id))
        return {"name": name, "actor": actor}

    def lease_acquire(self, concept_ids, owner, ttl_seconds=900, run_id="", request_id="",
                      actor="agent"):
        self.calls.append((concept_ids, owner, actor))
        return {"owner": owner}

    def provision(self, wait_seconds=0):
        return {"wait": wait_seconds}

    def queue_recover(self, concept_id, expected_queue_revision, reason, actor="agent",
                      request_id=""):
        return {"recovered": True, "actor": actor}


def test_reader_denied_before_mutation_and_actor_is_capability_bound():
    store = Store()
    service = Service(store=store, config={}, bridge={})
    with pytest.raises(PermissionError):
        service.dispatch("concept_create", {"name": "x"}, role="read")
    assert store.calls == []
    value = service.dispatch("concept_create", {"name": "x", "actor": "forged-admin"},
                             role="write", actor="mcp-writer")
    assert value["actor"] == "mcp-writer"
    with pytest.raises(PermissionError):
        service.dispatch("provision", {}, role="write")
    assert service.dispatch("provision", {"wait_seconds": 5}, role="admin") == {"wait": 5}


def test_local_coordination_is_not_a_remote_writer_operation():
    service = Service(store=Store(), config={}, bridge={
        "coordinate": lambda store, action, actor: {"action": action, "actor": actor},
    })
    for role, actor in [("write", "mcp-writer"), ("admin", "mcp-forgery")]:
        with pytest.raises(PermissionError):
            service.dispatch("coordinate", {"action": "acquire"}, role=role, actor=actor)
    result = service.dispatch("coordinate", {"action": "acquire"}, role="admin",
                              actor="local-admin")
    assert result == {"action": "acquire", "actor": "local-admin"}


def test_queue_recovery_requires_local_admin_and_integer_revision():
    service = Service(store=Store(), config={}, bridge={})
    args = {"concept_id": "c:x", "expected_queue_revision": 2, "reason": "Owner recovery"}
    for role, actor in [("read", "local-read"), ("write", "local-write"), ("admin", "mcp-admin")]:
        with pytest.raises(PermissionError):
            service.dispatch("queue_recover", args, role=role, actor=actor)
    assert service.dispatch("queue_recover", args, role="admin",
                             actor="local-admin")["recovered"]
    with pytest.raises(ValueError):
        service.dispatch("queue_recover", {**args, "expected_queue_revision": True},
                         role="admin", actor="local-admin")


def test_publisher_is_fixed_trusted_callback_not_a_remote_command():
    calls = []

    def publish(store, concept_id, expected_revision, lease_token, owner, actor, request_id=""):
        calls.append((concept_id, expected_revision, owner, actor))
        return {"job_id": "publication-1"}

    service = Service(store=Store(), config={}, bridge={"publish": publish})
    args = {"concept_id": "c:x", "expected_revision": 2, "lease_token": "opaque", "owner": "x"}
    with pytest.raises(PermissionError):
        service.dispatch("publish", args, role="read")
    assert service.dispatch("publish", args, role="write", actor="mcp-writer")["job_id"]
    assert calls == [("c:x", 2, "x", "mcp-writer")]
    with pytest.raises(TypeError):
        service.dispatch("publish", {**args, "command": ["touch", "forged"]}, role="write")


def test_owner_local_transport_preserves_legacy_namespace():
    store = Store()
    service = Service(store=store, config={}, bridge={})
    result = service.dispatch("lease_acquire", {
        "concept_ids": ["c:x"], "owner": "legacy:owned-run",
    }, role="admin", actor="local-admin")
    assert result["owner"] == "legacy:owned-run" and store.calls[-1][2] == "local-admin"


@pytest.mark.parametrize("arguments", [
    {"filters": {"$where": "malicious"}}, {"patch": {"source.path": "arbitrary"}},
    {"query": ""}, {"top": True}, {"limit": 201}, {"expected_revision": -1},
    {"ttl_seconds": 3601}, {"scope_ids": ["x"] * 101}, {"mode": "arbitrary_pipeline"},
    {"breadth": "unbounded"}, {"x": float("nan")},
])
def test_request_rejects_operators_bounds_and_nonfinite_json(arguments):
    with pytest.raises((ValueError, TypeError)):
        validate_arguments(arguments)


def test_unknown_operation_never_opens_database_and_binding_is_once():
    service = Service(config={}, bridge={})
    with pytest.raises(ValueError):
        service.dispatch("drop_database", {}, role="admin")
    assert service._store is None
    calls = []
    service = Service(store=Store(), config={}, bridge={"bind_store": calls.append})
    assert service.dispatch("status", {})["ready"]
    assert service.dispatch("status", {})["ready"]
    assert calls == [service.store]


def test_backend_driver_error_is_never_echoed():
    credential = "mongodb://secret-user:private-password@private-host/"
    for cls in [RuntimeError, ValueError, KeyError]:
        assert credential not in public_error(cls(credential))
