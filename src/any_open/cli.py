"""Command-line entry point for anyopen."""

import argparse
import os
import shlex
import shutil
import subprocess
import sys

from . import __version__
from .detect import LINUX, WINDOWS, detect_platform
from .plan import NoOpenerError, PlanError, build_command
from .target import TargetError, normalize


def wslpath(path):
    """Convert a Linux path to a Windows one with WSL's wslpath tool."""
    try:
        out = subprocess.run(["wslpath", "-w", path], capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError) as e:
        raise PlanError(f"wslpath could not convert {path}: {e}") from e
    return out.stdout.strip()


def run(command):
    """Run a Command and return its exit code."""
    if command.detach:
        subprocess.Popen(
            command.argv,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return 0
    return subprocess.run(command.argv).returncode


def make_parser():
    p = argparse.ArgumentParser(
        prog="anyopen",
        description="Open files, folders and URLs in their default application.",
    )
    p.add_argument(
        "targets", nargs="+", metavar="TARGET",
        help="file, folder or URL to open; - reads targets from stdin, one per line",
    )
    how = p.add_mutually_exclusive_group()
    how.add_argument(
        "-w", "--with", dest="app", metavar="APP",
        help="open in APP instead of the default application",
    )
    how.add_argument(
        "-r", "--reveal", action="store_true",
        help="show the target in the file manager instead of opening it",
    )
    p.add_argument(
        "-n", "--dry-run", action="store_true",
        help="print the command for each target instead of running it",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return p


def format_command(command, platform):
    if platform == WINDOWS:
        return subprocess.list2cmdline(command.argv)
    return shlex.join(command.argv)


def headless_hint(platform, environ):
    """Return a hint for when no opener was found, or None."""
    if platform != LINUX or environ.get("DISPLAY") or environ.get("WAYLAND_DISPLAY"):
        return None
    return (
        "anyopen: hint: no graphical session either (DISPLAY and WAYLAND_DISPLAY are unset), "
        "so there may be nothing to open things in; use --dry-run to print the command "
        "or --with APP to run a program directly"
    )


def open_one(raw, args, platform, runner, which, winpath, cwd, environ):
    """Open one target. Return True if it worked."""
    try:
        target = normalize(raw, cwd=cwd)
        command = build_command(platform, target, which, winpath, app=args.app, reveal=args.reveal)
    except (PlanError, TargetError) as e:
        print(f"anyopen: {e}", file=sys.stderr)
        hint = headless_hint(platform, environ) if isinstance(e, NoOpenerError) else None
        if hint:
            print(hint, file=sys.stderr)
        return False
    if args.dry_run:
        print(format_command(command, platform))
        return True
    try:
        code = runner(command)
    except OSError as e:
        print(f"anyopen: could not run {command.argv[0]}: {e}", file=sys.stderr)
        return False
    if code != 0 and not command.ignore_exit:
        print(f"anyopen: {command.argv[0]} exited with {code} for {raw}", file=sys.stderr)
        return False
    return True


def expand_stdin(targets, stdin):
    """Replace each "-" in `targets` with the non-blank lines read from `stdin`."""
    out = []
    for raw in targets:
        if raw == "-":
            # Only strip the line ending: names may start or end with spaces.
            out.extend(line.rstrip("\r\n") for line in stdin if line.strip())
        else:
            out.append(raw)
    return out


def main(argv=None, runner=run, platform=None, which=shutil.which, winpath=wslpath, cwd=None,
         environ=None):
    args = make_parser().parse_args(argv)
    if platform is None:
        platform = detect_platform()
    if environ is None:
        environ = os.environ
    ok = True
    for raw in expand_stdin(args.targets, sys.stdin):
        # Keep going after a failure so one bad target doesn't block the rest.
        if not open_one(raw, args, platform, runner, which, winpath, cwd, environ):
            ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
