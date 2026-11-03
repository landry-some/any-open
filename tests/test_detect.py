from any_open.detect import LINUX, MACOS, WINDOWS, WSL, detect_platform


def test_macos():
    assert detect_platform("darwin", {}, "") == MACOS


def test_windows_and_cygwin():
    assert detect_platform("win32", {}, "") == WINDOWS
    assert detect_platform("cygwin", {}, "") == WINDOWS


def test_plain_linux():
    assert detect_platform("linux", {}, "6.8.0-generic") == LINUX


def test_wsl_from_env():
    assert detect_platform("linux", {"WSL_DISTRO_NAME": "Ubuntu"}, "") == WSL
    assert detect_platform("linux", {"WSL_INTEROP": "/run/WSL/1_interop"}, "") == WSL


def test_wsl_from_kernel_release():
    assert detect_platform("linux", {}, "5.15.153.1-microsoft-standard-WSL2") == WSL
    assert detect_platform("linux", {}, "4.4.0-19041-Microsoft") == WSL


def test_other_unix_falls_back_to_linux():
    assert detect_platform("freebsd14", {}, "") == LINUX
