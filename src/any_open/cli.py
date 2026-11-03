"""Command-line entry point for anyopen."""

import argparse
import shutil
import subprocess
import sys

from . import __version__
from .detect import detect_platform
from .plan import NoOpenerError, build_command


def wslpath(path):
    out = subprocess.run(["wslpath", "-w", path], capture_output=True, text=True, check=True)
    return out.stdout.strip()


def run(command):
    """Run a Command and return its exit code."""
    return subprocess.run(command.argv).returncode


def make_parser():
    p = argparse.ArgumentParser(
        prog="anyopen",
        description="Open a file, folder or URL in its default application.",
    )
    p.add_argument("target", help="file, folder or URL to open")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return p


def main(argv=None, runner=run, platform=None, which=shutil.which, winpath=wslpath):
    args = make_parser().parse_args(argv)
    if platform is None:
        platform = detect_platform()
    try:
        command = build_command(platform, args.target, which, winpath)
    except NoOpenerError as e:
        print(f"anyopen: {e}", file=sys.stderr)
        return 1
    try:
        code = runner(command)
    except OSError as e:
        print(f"anyopen: could not run {command.argv[0]}: {e}", file=sys.stderr)
        return 1
    return 0 if code == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
