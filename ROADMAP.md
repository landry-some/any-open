# Roadmap

## v0.1

- [x] Pick the opener for macOS, Linux, Windows and WSL
- [x] Normalize targets: paths, `file://` URLs, other URLs
- [x] `--with APP` to open in a specific application
- [x] `--reveal` to show a file in the file manager
- [x] `--dry-run` and several targets in one call

## After v0.1 (about 32 hours)

### Features

- [ ] Config file with per-extension app overrides (~4 h)
- [ ] Linux `--reveal` that selects the file through the D-Bus FileManager1 interface (~3 h)
- [ ] `--wait` to block until the app closes, where the platform supports it (~2 h)
- [x] Read targets from stdin, one per line (~1.5 h)
- [ ] `--print-opener` diagnostics: detected platform and the commands found on PATH (~1.5 h)

### Bugs and edge cases

- [ ] Quoting of paths with spaces, `&` and `^` when going through `cmd /c start` (~2.5 h)
- [ ] WSL paths that only exist on the Linux side (`\\wsl$\...`) (~2 h)
- [x] Headless Linux with no opener installed: clear message and hint (~1 h)
- [x] Bare domains such as `example.com` treated as URLs when no such file exists (~1 h)

### Refactors

- [ ] Platform backends as a lookup table instead of if-chains (~2 h)
- [ ] Separate the planning and running layers so errors name the failed command (~1.5 h)

### Tests

- [ ] Subprocess-level tests with fake opener scripts on PATH (~3 h)
- [ ] GitHub Actions matrix on Linux, macOS and Windows (~2.5 h)

### Docs

- [ ] Per-platform behavior table in the README (~1.5 h)
- [ ] More `--help` examples and a short man page (~1 h)
- [ ] Shell completion scripts for bash, zsh and fish (~2 h)
