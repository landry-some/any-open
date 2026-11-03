from any_open.cli import main
from any_open.detect import LINUX, MACOS


def which_only(*names):
    return lambda name: f"/usr/bin/{name}" if name in names else None


class Recorder:
    def __init__(self, code=0):
        self.code = code
        self.calls = []

    def __call__(self, command):
        self.calls.append(command.argv)
        return self.code


def test_runs_the_opener():
    rec = Recorder()
    assert main(["notes.txt"], runner=rec, platform=MACOS, which=which_only()) == 0
    assert rec.calls == [["open", "notes.txt"]]


def test_opener_failure_gives_exit_1():
    rec = Recorder(code=4)
    assert main(["notes.txt"], runner=rec, platform=MACOS, which=which_only()) == 1


def test_missing_opener_is_reported(capsys):
    rec = Recorder()
    assert main(["notes.txt"], runner=rec, platform=LINUX, which=which_only()) == 1
    assert rec.calls == []
    assert "no opener found" in capsys.readouterr().err


def test_unrunnable_opener_is_reported(capsys):
    def boom(command):
        raise FileNotFoundError(2, "No such file or directory")

    assert main(["notes.txt"], runner=boom, platform=MACOS, which=which_only()) == 1
    assert "could not run open" in capsys.readouterr().err
