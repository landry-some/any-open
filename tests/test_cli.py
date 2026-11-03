import sys
import time

from any_open.cli import main, run
from any_open.detect import LINUX, MACOS
from any_open.plan import Command


def which_only(*names):
    return lambda name: f"/usr/bin/{name}" if name in names else None


class Recorder:
    def __init__(self, code=0):
        self.code = code
        self.calls = []

    def __call__(self, command):
        self.calls.append(command.argv)
        return self.code


def test_runs_the_opener_with_absolute_path(tmp_path):
    (tmp_path / "notes.txt").write_text("hi")
    rec = Recorder()
    code = main(["notes.txt"], runner=rec, platform=MACOS, which=which_only(), cwd=str(tmp_path))
    assert code == 0
    assert rec.calls == [["open", str(tmp_path / "notes.txt")]]


def test_url_is_passed_through():
    rec = Recorder()
    assert main(["https://example.com"], runner=rec, platform=MACOS, which=which_only()) == 0
    assert rec.calls == [["open", "https://example.com"]]


def test_missing_path_is_reported(tmp_path, capsys):
    rec = Recorder()
    code = main(["nope.txt"], runner=rec, platform=MACOS, which=which_only(), cwd=str(tmp_path))
    assert code == 1
    assert rec.calls == []
    assert "no such file or folder: nope.txt" in capsys.readouterr().err


def test_opener_failure_gives_exit_1():
    rec = Recorder(code=4)
    assert main(["https://example.com"], runner=rec, platform=MACOS, which=which_only()) == 1


def test_missing_opener_is_reported(capsys):
    rec = Recorder()
    assert main(["https://example.com"], runner=rec, platform=LINUX, which=which_only()) == 1
    assert rec.calls == []
    assert "no opener found" in capsys.readouterr().err


def test_unrunnable_opener_is_reported(capsys):
    def boom(command):
        raise FileNotFoundError(2, "No such file or directory")

    assert main(["https://example.com"], runner=boom, platform=MACOS, which=which_only()) == 1
    assert "could not run open" in capsys.readouterr().err


def test_with_option(tmp_path):
    (tmp_path / "a.md").write_text("x")
    rec = Recorder()
    code = main(["--with", "Typora", "a.md"], runner=rec, platform=MACOS, which=which_only(), cwd=str(tmp_path))
    assert code == 0
    assert rec.calls == [["open", "-a", "Typora", str(tmp_path / "a.md")]]


def test_detached_run_does_not_wait(tmp_path):
    marker = tmp_path / "started"
    script = f"import pathlib, time; pathlib.Path({str(marker)!r}).write_text('ok'); time.sleep(3)"
    start = time.monotonic()
    assert run(Command([sys.executable, "-c", script], detach=True)) == 0
    assert time.monotonic() - start < 2
    for _ in range(50):
        if marker.exists():
            break
        time.sleep(0.05)
    assert marker.read_text() == "ok"
