"""Turn a target into the native command that opens it."""

from dataclasses import dataclass

from .detect import LINUX, MACOS, WINDOWS, WSL


class NoOpenerError(Exception):
    """No usable opener command was found on this system."""


@dataclass(frozen=True)
class Command:
    argv: list


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


def build_command(platform, target, which, winpath=None):
    """Build the Command that opens `target` (a Target) on `platform`.

    On WSL, explorer.exe needs a Windows path; `winpath` converts a Linux path
    to one (normally by calling `wslpath -w`). URLs are passed as they are.
    """
    opener = resolve_opener(platform, which)
    value = target.value
    if opener == ["explorer.exe"] and not target.is_url and winpath is not None:
        value = winpath(value)
    return Command(opener + [value])
