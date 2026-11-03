import pytest

from any_open.detect import LINUX, MACOS, WINDOWS, WSL
from any_open.plan import NoOpenerError, build_command, resolve_opener
from any_open.target import Target


def which_only(*names):
    return lambda name: f"/usr/bin/{name}" if name in names else None


def path(p):
    return Target(p, is_url=False)


def fake_winpath(path):
    return "\\\\wsl.localhost\\Ubuntu" + path.replace("/", "\\")


def test_macos_uses_open():
    assert build_command(MACOS, path("/tmp/a.txt"), which_only()).argv == ["open", "/tmp/a.txt"]


def test_windows_uses_start_with_empty_title():
    cmd = build_command(WINDOWS, path("C:\\a b.txt"), which_only())
    assert cmd.argv == ["cmd", "/c", "start", "", "C:\\a b.txt"]


def test_linux_prefers_xdg_open():
    assert resolve_opener(LINUX, which_only("xdg-open", "gio")) == ["xdg-open"]


def test_linux_falls_back_to_gio():
    assert resolve_opener(LINUX, which_only("gio")) == ["gio", "open"]


def test_linux_without_opener_raises():
    with pytest.raises(NoOpenerError, match="xdg-utils"):
        resolve_opener(LINUX, which_only())


def test_wsl_prefers_wslview_and_keeps_linux_path():
    cmd = build_command(WSL, path("/home/me/a.txt"), which_only("wslview"), fake_winpath)
    assert cmd.argv == ["wslview", "/home/me/a.txt"]


def test_wsl_explorer_gets_windows_path():
    cmd = build_command(WSL, path("/home/me/a.txt"), which_only(), fake_winpath)
    assert cmd.argv == ["explorer.exe", "\\\\wsl.localhost\\Ubuntu\\home\\me\\a.txt"]


def test_wsl_explorer_passes_urls_untouched():
    url = Target("https://example.com/a b", is_url=True)
    cmd = build_command(WSL, url, which_only(), fake_winpath)
    assert cmd.argv == ["explorer.exe", "https://example.com/a b"]


def test_unknown_platform():
    with pytest.raises(ValueError):
        resolve_opener("plan9", which_only())
