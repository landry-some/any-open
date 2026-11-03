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
anyopen README.md                    # open a file in its default app
anyopen . https://example.com        # several targets, opened in order
anyopen --with gedit notes.txt       # open in a chosen app (-w)
anyopen --reveal ~/Downloads/a.pdf   # show it in the file manager (-r)
anyopen --dry-run report.pdf         # print the command, run nothing (-n)
```

Paths are expanded (`~`) and made absolute, and must exist. `file://` URLs are turned
into paths. Anything else that looks like a URL (`https:`, `mailto:`, `vscode:`, ...)
is passed to the opener as it is.

If one target fails, the others are still opened and `anyopen` exits with 1.
`--with` and `--reveal` can't be combined.

### What it runs on each platform

| Platform | Default | `--with APP` | `--reveal` |
|---|---|---|---|
| macOS | `open T` | `open -a APP T` | `open -R T` |
| Linux | `xdg-open T`, or `gio open T` | `APP T` (started in the background) | opens the parent folder |
| Windows | `cmd /c start "" T` | `cmd /c start "" APP T` | `explorer /select,T` |
| WSL | `wslview T`, or `explorer.exe T` | `cmd.exe /c start "" APP T` | `explorer.exe /select,T` |

On WSL, paths given to Windows programs are converted with `wslpath -w` first.
`wslview` (from wslu) takes Linux paths itself. WSL is detected from the
`WSL_DISTRO_NAME`/`WSL_INTEROP` variables or the kernel release string.

## Test

```bash
pytest
```

The tests don't open anything: they check the command that would be run on each
platform, with fake lookups in place of the real openers. So far they have only been
run on Linux.

The planned work is in [ROADMAP.md](ROADMAP.md).

## License

MIT, see [LICENSE](LICENSE).
