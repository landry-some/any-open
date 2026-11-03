import pytest

from any_open.detect import LINUX, MACOS, WINDOWS, WSL
from any_open.plan import NoOpenerError, PlanError, build_command, resolve_opener
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


URL = Target("https://example.com", is_url=True)


def test_with_app_macos():
    cmd = build_command(MACOS, path("/tmp/a.txt"), which_only(), app="TextEdit")
    assert cmd.argv == ["open", "-a", "TextEdit", "/tmp/a.txt"]
    assert not cmd.detach


def test_with_app_windows():
    cmd = build_command(WINDOWS, path("C:\\a.txt"), which_only(), app="notepad")
    assert cmd.argv == ["cmd", "/c", "start", "", "notepad", "C:\\a.txt"]


def test_with_app_linux_launches_directly_and_detaches():
    cmd = build_command(LINUX, path("/tmp/a.txt"), which_only(), app="gedit")
    assert cmd.argv == ["gedit", "/tmp/a.txt"]
    assert cmd.detach


def test_with_app_linux_needs_no_opener():
    # Direct launch works even when xdg-open and gio are missing.
    assert build_command(LINUX, URL, which_only(), app="firefox").argv == ["firefox", URL.value]


def test_with_app_wsl_translates_path():
    cmd = build_command(WSL, path("/home/me/a.txt"), which_only("wslview"), fake_winpath, app="notepad.exe")
    assert cmd.argv == [
        "cmd.exe", "/c", "start", "", "notepad.exe", "\\\\wsl.localhost\\Ubuntu\\home\\me\\a.txt",
    ]


def test_with_app_wsl_keeps_url():
    cmd = build_command(WSL, URL, which_only(), fake_winpath, app="msedge")
    assert cmd.argv[-1] == URL.value


def test_reveal_macos():
    assert build_command(MACOS, path("/tmp/a.txt"), which_only(), reveal=True).argv == ["open", "-R", "/tmp/a.txt"]


def test_reveal_windows_selects_file_and_ignores_exit():
    cmd = build_command(WINDOWS, path("C:\\dir\\a.txt"), which_only(), reveal=True)
    assert cmd.argv == ["explorer", "/select,C:\\dir\\a.txt"]
    assert cmd.ignore_exit


def test_reveal_wsl_uses_windows_path():
    cmd = build_command(WSL, path("/home/me/a.txt"), which_only("wslview"), fake_winpath, reveal=True)
    assert cmd.argv == ["explorer.exe", "/select,\\\\wsl.localhost\\Ubuntu\\home\\me\\a.txt"]
    assert cmd.ignore_exit


def test_reveal_linux_opens_parent_folder():
    cmd = build_command(LINUX, path("/home/me/a.txt"), which_only("xdg-open"), reveal=True)
    assert cmd.argv == ["xdg-open", "/home/me"]


def test_reveal_linux_folder_opens_its_parent():
    cmd = build_command(LINUX, path("/home/me/"), which_only("gio"), reveal=True)
    assert cmd.argv == ["gio", "open", "/home"]


def test_reveal_linux_root():
    assert build_command(LINUX, path("/"), which_only("xdg-open"), reveal=True).argv == ["xdg-open", "/"]


def test_reveal_url_is_an_error():
    with pytest.raises(PlanError, match="can't reveal a URL"):
        build_command(MACOS, URL, which_only(), reveal=True)


def test_reveal_with_app_is_an_error():
    with pytest.raises(PlanError):
        build_command(MACOS, path("/tmp/a"), which_only(), app="X", reveal=True)
