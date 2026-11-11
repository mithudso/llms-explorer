"""Private artifact writes cannot follow a planted link before rejecting it."""

from pathlib import Path

import pytest

from explorer_api import artifacts


@pytest.mark.parametrize("link_at", ["leaf", "section", "artifact", "user"])
def test_write_refuses_symlinks_without_touching_outside(tmp_path, link_at):
    stores = tmp_path / "stores"
    outside = tmp_path / "outside"
    outside.mkdir()
    untouched = outside / "llms.txt"
    untouched.write_bytes(b"private original")
    root = artifacts.artifact_dir(stores, "usr_owner", "notes")
    relative = "llms.txt"
    if link_at == "leaf":
        root.mkdir(parents=True)
        (root / "llms.txt").symlink_to(untouched)
    elif link_at == "section":
        root.mkdir(parents=True)
        (root / "section").symlink_to(outside, target_is_directory=True)
        relative = "section/llms.txt"
    elif link_at == "artifact":
        root.parent.mkdir(parents=True)
        root.symlink_to(outside, target_is_directory=True)
    else:
        stores.mkdir()
        (stores / "usr_owner").symlink_to(outside, target_is_directory=True)

    with pytest.raises(artifacts.NotFound):
        artifacts.write(stores, "usr_owner", "notes", relative, b"must not escape")

    assert untouched.read_bytes() == b"private original"
    assert list(outside.iterdir()) == [untouched]


def test_write_creates_and_replaces_only_the_owned_regular_file(tmp_path):
    stores = tmp_path / "stores"
    path = artifacts.write(stores, "usr_owner", "notes", "section/llms.txt", "first")
    assert isinstance(path, Path)
    assert path.read_text() == "first"
    assert artifacts.write(stores, "usr_owner", "notes", "section/llms.txt", b"second") == path
    assert path.read_bytes() == b"second"
    assert list(path.parent.iterdir()) == [path]


def test_read_refuses_a_symlinked_artifact_root(tmp_path):
    stores = tmp_path / "stores"
    outside = tmp_path / "another-user"
    outside.mkdir()
    (outside / "llms.txt").write_bytes(b"another user's private content")
    root = artifacts.artifact_dir(stores, "usr_owner", "notes")
    root.parent.mkdir(parents=True)
    root.symlink_to(outside, target_is_directory=True)

    with pytest.raises(artifacts.NotFound):
        artifacts.read(stores, "usr_owner", "notes", "llms.txt")


def test_failed_atomic_publication_preserves_existing_bytes(tmp_path, monkeypatch):
    stores = tmp_path / "stores"
    path = artifacts.write(stores, "usr_owner", "notes", "llms.txt", b"original")

    def unavailable(*args, **kwargs):
        raise OSError("synthetic publication failure")

    monkeypatch.setattr(artifacts.os, "replace", unavailable)
    with pytest.raises(artifacts.NotFound):
        artifacts.write(stores, "usr_owner", "notes", "llms.txt", b"replacement")

    assert path.read_bytes() == b"original"
    assert list(path.parent.iterdir()) == [path]


@pytest.mark.parametrize("swap", ["leaf", "ancestor"])
def test_read_cannot_follow_a_path_swapped_at_open(tmp_path, monkeypatch, swap):
    stores = tmp_path / "stores"
    leaf = artifacts.write(stores, "usr_owner", "notes", "section/llms.txt", b"owned")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "llms.txt").write_bytes(b"outside private content")
    real_os_open = artifacts.os.open
    real_path_open = Path.open
    swapped = False

    def replace_path():
        nonlocal swapped
        if swapped:
            return
        swapped = True
        if swap == "leaf":
            leaf.unlink()
            leaf.symlink_to(outside / "llms.txt")
        else:
            leaf.parent.rename(leaf.parent.with_name("pinned-section"))
            leaf.parent.symlink_to(outside, target_is_directory=True)

    def descriptor_open(path, flags, *args, **kwargs):
        if path == "llms.txt" and kwargs.get("dir_fd") is not None:
            replace_path()
        return real_os_open(path, flags, *args, **kwargs)

    def pathname_open(path, *args, **kwargs):
        if path == leaf:
            replace_path()
        return real_path_open(path, *args, **kwargs)

    # Cover both the vulnerable pathname reopen and the repaired descriptor
    # open at the same logical boundary, without replacing their actual I/O.
    monkeypatch.setattr(artifacts.os, "open", descriptor_open)
    monkeypatch.setattr(Path, "open", pathname_open)
    try:
        served = artifacts.read(stores, "usr_owner", "notes", "section/llms.txt")
    except artifacts.NotFound:
        pass
    else:
        assert served.data == b"owned"
    assert swapped, "the race must occur at the active implementation's open"


@pytest.mark.parametrize("operation", ["read", "write"])
def test_fdopen_failure_closes_raw_descriptor(tmp_path, monkeypatch, operation):
    stores = tmp_path / "stores"
    leaf = artifacts.write(stores, "usr_owner", "notes", "llms.txt", b"original")
    opened = []

    def unavailable(fd, *args, **kwargs):
        opened.append(fd)
        raise OSError("synthetic file wrapper allocation failure")

    monkeypatch.setattr(artifacts.os, "fdopen", unavailable)
    with pytest.raises(artifacts.NotFound):
        if operation == "read":
            artifacts.read(stores, "usr_owner", "notes", "llms.txt")
        else:
            artifacts.write(stores, "usr_owner", "notes", "llms.txt", b"replacement")
    assert len(opened) == 1
    with pytest.raises(OSError):
        artifacts.os.fstat(opened[0])
    assert leaf.read_bytes() == b"original"
    assert list(leaf.parent.iterdir()) == [leaf]


@pytest.mark.parametrize("operation", ["read", "write"])
@pytest.mark.parametrize("field", ["user_id", "slug", "section"])
def test_final_newline_components_refuse_before_private_file_access(tmp_path, operation, field):
    user_id = "usr_owner\n" if field == "user_id" else "usr_owner"
    slug = "notes\n" if field == "slug" else "notes"
    relative = "section\n/llms.txt" if field == "section" else "llms.txt"
    path = tmp_path / user_id / "artifacts" / f"{slug}.llms" / relative
    path.parent.mkdir(parents=True)
    path.write_bytes(b"private original")
    with pytest.raises(artifacts.NotFound):
        if operation == "read":
            artifacts.read(tmp_path, user_id, slug, relative)
        else:
            artifacts.write(tmp_path, user_id, slug, relative, b"replacement")
    assert path.read_bytes() == b"private original"


@pytest.mark.parametrize("relative", ["llms.txt", "/llms.txt/", "section.v1_2-3//llms.txt/"])
def test_long_valid_slug_and_normalized_sections_keep_round_trip_contract(tmp_path, relative):
    slug = "n" * 201
    artifacts.write(tmp_path, "usr_owner", slug, relative, b"bounded content")
    served = artifacts.read(tmp_path, "usr_owner", slug, relative)
    assert served.data == b"bounded content"
    assert served.path.is_relative_to(tmp_path / "usr_owner" / "artifacts")
