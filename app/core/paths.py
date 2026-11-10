import os
import uuid

ALLOWED_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".webm"}


def resolve_in_dir(base_dir: str, name: str) -> str:
    """Resolve name under base_dir; raise ValueError if it escapes."""
    base = os.path.realpath(base_dir)
    path = os.path.realpath(os.path.join(base, name))
    if os.path.commonpath([base, path]) != base:
        raise ValueError("path escapes upload dir")
    return path


def new_upload_name(original_name: str) -> str:
    """Server-generated name: uuid + whitelisted extension from the client name."""
    ext = os.path.splitext(original_name or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"extension not allowed: {ext!r}")
    return uuid.uuid4().hex + ext
