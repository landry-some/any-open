"""Command-line entry point for anyopen."""

import argparse
import shutil
import subprocess
import sys

from . import __version__
from .detect import detect_platform
from .plan import PlanError, build_command
from .target import TargetError, normalize


def wslpath(path):
    out = subprocess.run(["wslpath", "-w", path], capture_output=True, text=True, check=True)
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
        description="Open a file, folder or URL in its default application.",
    )
    p.add_argument("target", help="file, folder or URL to open")
    how = p.add_mutually_exclusive_group()
    how.add_argument(
        "-w", "--with", dest="app", metavar="APP",
        help="open in APP instead of the default application",
    )
    how.add_argument(
        "-r", "--reveal", action="store_true",
        help="show the target in the file manager instead of opening it",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return p


def main(argv=None, runner=run, platform=None, which=shutil.which, winpath=wslpath, cwd=None):
    args = make_parser().parse_args(argv)
    if platform is None:
        platform = detect_platform()
    try:
        target = normalize(args.target, cwd=cwd)
        command = build_command(platform, target, which, winpath, app=args.app, reveal=args.reveal)
    except (PlanError, TargetError) as e:
        print(f"anyopen: {e}", file=sys.stderr)
        return 1
    try:
        code = runner(command)
    except OSError as e:
        print(f"anyopen: could not run {command.argv[0]}: {e}", file=sys.stderr)
        return 1
    return 0 if code == 0 or command.ignore_exit else 1


if __name__ == "__main__":
    sys.exit(main())
