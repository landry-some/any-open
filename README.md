# any-open

`anyopen` opens files, folders and URLs in their default application with one command
that behaves the same on macOS, Linux, Windows and WSL. It works out which native
opener to call (`open`, `xdg-open`, `gio open`, `cmd /c start`, `wslview`,
`explorer.exe`) and how to pass the target to it.

It's for people who move between machines and want the same command in their shell
and scripts everywhere, instead of remembering which opener each OS has.

Built with Python 3.11+ and the standard library only. Tests use pytest.

## Install

```bash
git clone https://github.com/landry-some/any-open.git
cd any-open
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
```

## Run

```bash
anyopen README.md
```

## Test

```bash
pytest
```

## License

MIT, see [LICENSE](LICENSE).
