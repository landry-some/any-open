"""Turn a target into the native command that opens it."""

from dataclasses import dataclass

from .detect import LINUX, MACOS, WINDOWS, WSL


class NoOpenerError(Exception):
    """No usable opener command was found on this system."""


@dataclass(frozen=True)
class Command:
    argv: list
    # Launch without waiting. Used when we start a GUI app directly, which
    # would otherwise keep the terminal busy until it closes.
    detach: bool = False


def resolve_opener(platform, which):
    """Return the base argv of the default opener for `platform`.

    `which` works like shutil.which: it takes a program name and returns a path
    or None.
    """
    if platform == MACOS:
        return ["open"]
    if platform == WINDOWS:
        # The empty string is the window title; without it start treats a
        # quoted target as the title.
        return ["cmd", "/c", "start", ""]
    if platform == WSL:
        if which("wslview"):
            return ["wslview"]
        return ["explorer.exe"]
    if platform == LINUX:
        if which("xdg-open"):
            return ["xdg-open"]
        if which("gio"):
            return ["gio", "open"]
        raise NoOpenerError("no opener found: install xdg-utils (xdg-open) or glib (gio)")
    raise ValueError(f"unknown platform: {platform}")


def _windows_value(target, winpath):
    if target.is_url or winpath is None:
        return target.value
    return winpath(target.value)


def build_command(platform, target, which, winpath=None, app=None):
    """Build the Command that opens `target` (a Target) on `platform`.

    With `app`, the target is opened in that application instead of the
    default one. On WSL, Windows programs need a Windows path; `winpath`
    converts a Linux path to one (normally by calling `wslpath -w`). URLs are
    passed as they are.
    """
    if app is not None:
        return _build_with_app(platform, target, app, winpath)

    opener = resolve_opener(platform, which)
    value = target.value
    if opener == ["explorer.exe"]:
        value = _windows_value(target, winpath)
    return Command(opener + [value])


def _build_with_app(platform, target, app, winpath):
    if platform == MACOS:
        return Command(["open", "-a", app, target.value])
    if platform == WINDOWS:
        return Command(["cmd", "/c", "start", "", app, target.value])
    if platform == WSL:
        # Assume a Windows app: Linux apps can be run directly without anyopen.
        return Command(["cmd.exe", "/c", "start", "", app, _windows_value(target, winpath)])
    if platform == LINUX:
        return Command([app, target.value], detach=True)
    raise ValueError(f"unknown platform: {platform}")
