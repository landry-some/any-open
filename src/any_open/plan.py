"""Turn a target into the native command that opens it."""

import os
from dataclasses import dataclass

from .detect import LINUX, MACOS, WINDOWS, WSL


class PlanError(Exception):
    """The target can't be opened the way it was asked."""


class NoOpenerError(PlanError):
    """No usable opener command was found on this system."""


@dataclass(frozen=True)
class Command:
    argv: list
    # Launch without waiting. Used when we start a GUI app directly, which
    # would otherwise keep the terminal busy until it closes.
    detach: bool = False
    # explorer.exe exits with 1 even when it worked, so its code means nothing.
    ignore_exit: bool = False


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


def build_command(platform, target, which, winpath=None, app=None, reveal=False):
    """Build the Command that opens `target` (a Target) on `platform`.

    With `app`, the target is opened in that application instead of the
    default one. On WSL, Windows programs need a Windows path; `winpath`
    converts a Linux path to one (normally by calling `wslpath -w`). URLs are
    passed as they are.

    With `reveal`, the target's folder is shown in the file manager, with the
    target selected where the platform supports it.
    """
    if reveal:
        if app is not None:
            raise PlanError("--reveal and --with can't be used together")
        return _build_reveal(platform, target, which, winpath)
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


def _build_reveal(platform, target, which, winpath):
    if target.is_url:
        raise PlanError(f"can't reveal a URL: {target.value}")
    if platform == MACOS:
        return Command(["open", "-R", target.value])
    if platform == WINDOWS:
        return Command(["explorer", "/select," + target.value], ignore_exit=True)
    if platform == WSL:
        value = _windows_value(target, winpath)
        return Command(["explorer.exe", "/select," + value], ignore_exit=True)
    if platform == LINUX:
        # No portable way to select a file, so open the folder that holds it.
        parent = os.path.dirname(target.value.rstrip("/")) or "/"
        return Command(resolve_opener(LINUX, which) + [parent])
    raise ValueError(f"unknown platform: {platform}")
