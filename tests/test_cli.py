import io
import sys
import time

import pytest

from any_open.cli import main, run
from any_open.detect import LINUX, MACOS, WINDOWS, WSL
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


def test_reveal_ignores_explorer_exit_code(tmp_path):
    (tmp_path / "a.txt").write_text("x")
    rec = Recorder(code=1)
    code = main(["--reveal", "a.txt"], runner=rec, platform=WINDOWS, which=which_only(), cwd=str(tmp_path))
    assert code == 0
    assert rec.calls[0][0] == "explorer"


def test_reveal_url_is_reported(capsys):
    rec = Recorder()
    assert main(["-r", "https://example.com"], runner=rec, platform=MACOS, which=which_only()) == 1
    assert "can't reveal a URL" in capsys.readouterr().err


def test_reveal_and_with_conflict(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["-r", "-w", "X", "https://example.com"], runner=Recorder(), platform=MACOS, which=which_only())
    assert exc.value.code == 2
    assert "not allowed with" in capsys.readouterr().err


def test_several_targets_open_in_order(tmp_path):
    (tmp_path / "a").write_text("x")
    rec = Recorder()
    code = main(["a", "https://example.com"], runner=rec, platform=MACOS, which=which_only(), cwd=str(tmp_path))
    assert code == 0
    assert rec.calls == [["open", str(tmp_path / "a")], ["open", "https://example.com"]]


def test_bad_target_does_not_stop_the_others(tmp_path, capsys):
    rec = Recorder()
    code = main(["missing", "https://example.com"], runner=rec, platform=MACOS, which=which_only(), cwd=str(tmp_path))
    assert code == 1
    assert rec.calls == [["open", "https://example.com"]]
    assert "missing" in capsys.readouterr().err


def test_failed_opener_names_the_target(capsys):
    rec = Recorder(code=3)
    assert main(["https://example.com"], runner=rec, platform=MACOS, which=which_only()) == 1
    assert "open exited with 3 for https://example.com" in capsys.readouterr().err


def test_dry_run_prints_and_runs_nothing(tmp_path, capsys):
    (tmp_path / "my file.txt").write_text("x")
    rec = Recorder()
    code = main(["-n", "my file.txt", "https://example.com"], runner=rec, platform=MACOS,
                which=which_only(), cwd=str(tmp_path))
    assert code == 0
    assert rec.calls == []
    out = capsys.readouterr().out.splitlines()
    assert out == [f"open '{tmp_path / 'my file.txt'}'", "open https://example.com"]


def test_dry_run_uses_windows_quoting(capsys):
    assert main(["--dry-run", "https://example.com/a b"], runner=Recorder(), platform=WINDOWS,
                which=which_only()) == 0
    assert capsys.readouterr().out.strip() == 'cmd /c start "" "https://example.com/a b"'


def test_dry_run_still_reports_bad_targets(tmp_path, capsys):
    assert main(["-n", "nope"], runner=Recorder(), platform=MACOS, which=which_only(), cwd=str(tmp_path)) == 1
    assert "no such file or folder" in capsys.readouterr().err


def test_no_targets_is_a_usage_error():
    with pytest.raises(SystemExit) as exc:
        main([], runner=Recorder(), platform=MACOS, which=which_only())
    assert exc.value.code == 2


def test_wslpath_failure_is_reported(tmp_path, capsys, monkeypatch):
    from any_open import cli

    def no_wslpath(*a, **k):
        raise FileNotFoundError(2, "No such file or directory", "wslpath")

    monkeypatch.setattr(cli.subprocess, "run", no_wslpath)
    (tmp_path / "a").write_text("x")
    code = main(["a"], runner=Recorder(), platform=WSL, which=which_only(), cwd=str(tmp_path))
    assert code == 1
    assert "wslpath could not convert" in capsys.readouterr().err


def test_dash_reads_targets_from_stdin(tmp_path, monkeypatch):
    (tmp_path / "a b.txt").write_text("x")
    monkeypatch.setattr(sys, "stdin", io.StringIO("a b.txt\n\n  \nhttps://example.com\r\n"))
    rec = Recorder()
    code = main(["-"], runner=rec, platform=MACOS, which=which_only(), cwd=str(tmp_path))
    assert code == 0
    assert rec.calls == [["open", str(tmp_path / "a b.txt")], ["open", "https://example.com"]]


def test_stdin_targets_keep_their_place(monkeypatch):
    monkeypatch.setattr(sys, "stdin", io.StringIO("https://b.example\n"))
    rec = Recorder()
    main(["https://a.example", "-", "https://c.example"], runner=rec, platform=MACOS, which=which_only())
    assert [argv[1] for argv in rec.calls] == ["https://a.example", "https://b.example", "https://c.example"]


def test_empty_stdin_opens_nothing(monkeypatch):
    monkeypatch.setattr(sys, "stdin", io.StringIO(""))
    rec = Recorder()
    assert main(["-"], runner=rec, platform=MACOS, which=which_only()) == 0
    assert rec.calls == []


def test_headless_linux_without_opener_gets_a_hint(capsys):
    code = main(["https://example.com"], runner=Recorder(), platform=LINUX, which=which_only(), environ={})
    assert code == 1
    err = capsys.readouterr().err.splitlines()
    assert err[0].startswith("anyopen: no opener found")
    assert "no graphical session" in err[1]
    assert "--dry-run" in err[1]


@pytest.mark.parametrize("env", [{"DISPLAY": ":0"}, {"WAYLAND_DISPLAY": "wayland-0"}])
def test_desktop_linux_without_opener_gets_no_hint(env, capsys):
    assert main(["https://example.com"], runner=Recorder(), platform=LINUX, which=which_only(), environ=env) == 1
    err = capsys.readouterr().err
    assert "no opener found" in err
    assert "hint" not in err


def test_headless_hint_only_for_missing_opener(tmp_path, capsys):
    assert main(["nope"], runner=Recorder(), platform=LINUX, which=which_only("xdg-open"),
                cwd=str(tmp_path), environ={}) == 1
    assert "hint" not in capsys.readouterr().err


def test_print_opener_linux(capsys):
    assert main(["--print-opener"], platform=LINUX, which=which_only("gio")) == 0
    assert capsys.readouterr().out.splitlines() == [
        "platform: linux",
        "opener: gio open",
        "xdg-open: not found",
        "gio: /usr/bin/gio",
    ]


def test_print_opener_without_any_opener(capsys):
    assert main(["--print-opener"], platform=LINUX, which=which_only()) == 0
    assert "opener: none found" in capsys.readouterr().out


def test_print_opener_wsl_lists_windows_tools(capsys):
    assert main(["--print-opener"], platform=WSL, which=which_only("wslpath", "explorer.exe")) == 0
    out = capsys.readouterr().out.splitlines()
    assert out[:2] == ["platform: wsl", "opener: explorer.exe"]
    assert "wslview: not found" in out
    assert "wslpath: /usr/bin/wslpath" in out


def test_print_opener_takes_no_targets(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--print-opener", "a"], platform=MACOS, which=which_only())
    assert exc.value.code == 2
    assert "takes no targets" in capsys.readouterr().err
