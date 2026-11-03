import os

import pytest

from any_open.target import Target, TargetError, normalize


def always(path):
    return True


def never(path):
    return False


def test_relative_path_made_absolute(tmp_path):
    (tmp_path / "a.txt").write_text("x")
    assert normalize("a.txt", cwd=str(tmp_path)) == Target(str(tmp_path / "a.txt"), False)


def test_dot_dot_is_collapsed(tmp_path):
    (tmp_path / "sub").mkdir()
    assert normalize("sub/..", cwd=str(tmp_path)).value == str(tmp_path)


def test_home_is_expanded(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    assert normalize("~/x", exists=always).value == os.path.join(str(tmp_path), "x")


def test_missing_path_raises(tmp_path):
    with pytest.raises(TargetError, match="no such file or folder: gone"):
        normalize("gone", cwd=str(tmp_path))


def test_empty_target_raises():
    with pytest.raises(TargetError):
        normalize("")


@pytest.mark.parametrize("url", [
    "https://example.com/a?b=1",
    "http://localhost:8000",
    "mailto:someone@example.com",
    "vscode://file/tmp/x",
    "ssh+git://example.com/repo",
])
def test_urls_pass_through(url):
    assert normalize(url, exists=never) == Target(url, True)


def test_file_url_becomes_path():
    assert normalize("file:///tmp/a%20b.txt", exists=always) == Target("/tmp/a b.txt", False)


def test_file_url_with_localhost():
    assert normalize("file://localhost/tmp/x", exists=always).value == "/tmp/x"


def test_file_url_on_other_host_raises():
    with pytest.raises(TargetError, match="another host"):
        normalize("file://server/share/x", exists=always)


def test_file_url_must_exist():
    with pytest.raises(TargetError):
        normalize("file:///definitely/not/here", exists=never)


def test_windows_drive_letter_is_not_a_url():
    # One-letter "schemes" are drive letters, so this is checked as a path.
    with pytest.raises(TargetError):
        normalize("C:\\no\\such\\file", exists=never)
