import pytest

from app.core.paths import new_upload_name, resolve_in_dir


def test_traversal_name_is_replaced_by_uuid(tmp_path):
    name = new_upload_name("../../x.mp4")
    assert "/" not in name and ".." not in name and name.endswith(".mp4")
    assert resolve_in_dir(str(tmp_path), name).startswith(str(tmp_path.resolve()))


def test_disallowed_extension():
    for bad in ("evil.sh", "noext", "a.mp4.exe"):
        with pytest.raises(ValueError):
            new_upload_name(bad)


def test_resolve_rejects_escape(tmp_path):
    for bad in ("../../x.mp4", "/etc/passwd"):
        with pytest.raises(ValueError):
            resolve_in_dir(str(tmp_path), bad)
