"""Work out which platform we're on, telling WSL apart from plain Linux."""

import os
import sys

MACOS = "macos"
LINUX = "linux"
WINDOWS = "windows"
WSL = "wsl"

_OSRELEASE = "/proc/sys/kernel/osrelease"


def _read_osrelease():
    try:
        with open(_OSRELEASE, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def detect_platform(sys_platform=None, environ=None, osrelease=None):
    """Return one of MACOS, LINUX, WINDOWS or WSL.

    The arguments default to the real system values; tests pass their own.
    """
    if sys_platform is None:
        sys_platform = sys.platform
    if environ is None:
        environ = os.environ

    if sys_platform == "darwin":
        return MACOS
    if sys_platform in ("win32", "cygwin"):
        return WINDOWS
    if sys_platform.startswith("linux"):
        if environ.get("WSL_DISTRO_NAME") or environ.get("WSL_INTEROP"):
            return WSL
        if osrelease is None:
            osrelease = _read_osrelease()
        if "microsoft" in osrelease.lower():
            return WSL
        return LINUX
    # BSDs and other unixes usually ship xdg-open too.
    return LINUX
