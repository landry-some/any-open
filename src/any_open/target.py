"""Normalize what the user typed into a path or a URL."""

import os
import re
from dataclasses import dataclass
from urllib.parse import unquote, urlparse

# A URL scheme needs at least two characters, so "C:\file" stays a path.
_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.\-]+:")

# "example.com", "www.example.org/a?b". Only checked when no such file
# exists, and only for common TLDs so a missing "notes.txt" stays a path error.
_DOMAIN = re.compile(
    r"^(?:[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?\.)+([A-Za-z]{2,})(?:[/?#].*)?$"
)
_TLDS = {
    "com", "org", "net", "edu", "gov", "io", "dev", "app", "ai", "co", "me",
    "info", "xyz", "uk", "de", "fr", "nl", "eu", "ca", "us", "jp", "au",
}


class TargetError(Exception):
    """The target can't be opened (e.g. the path does not exist)."""


@dataclass(frozen=True)
class Target:
    value: str
    is_url: bool


def _file_url_to_path(raw):
    parts = urlparse(raw)
    if parts.netloc not in ("", "localhost"):
        raise TargetError(f"file URL on another host is not supported: {raw}")
    path = unquote(parts.path)
    # file:///C:/x on Windows parses to "/C:/x".
    if re.match(r"^/[A-Za-z]:", path):
        path = path[1:]
    return path


def _is_bare_domain(raw):
    m = _DOMAIN.match(raw)
    return bool(m) and m.group(1).lower() in _TLDS


def normalize(raw, cwd=None, exists=os.path.exists):
    """Return a Target for `raw`.

    Paths are expanded (~) and made absolute against `cwd` and must exist.
    file:// URLs are turned into paths. Any other URL is passed through.
    A bare domain such as example.com becomes an https:// URL, but only when
    no file or folder of that name exists.
    """
    if not raw:
        raise TargetError("empty target")
    if raw.lower().startswith("file:"):
        raw = _file_url_to_path(raw)
    elif _SCHEME.match(raw):
        return Target(raw, is_url=True)

    path = os.path.expanduser(raw)
    if cwd is not None and not os.path.isabs(path):
        path = os.path.join(cwd, path)
    path = os.path.abspath(path)
    if not exists(path):
        if _is_bare_domain(raw):
            return Target("https://" + raw, is_url=True)
        raise TargetError(f"no such file or folder: {raw}")
    return Target(path, is_url=False)
