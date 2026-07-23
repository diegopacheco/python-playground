# python-essentials-distro

Detect the operating system distribution with the `distro` library, the modern replacement for the removed `platform.linux_distribution()`.

### What it does

`src/main.py` reads the OS release metadata and prints the distribution id, pretty name, version, codename, the ids it is "like", and the full info dict.

### Features

- Distribution id, name, version, major version, codename
- `like()` for derivative distributions (for example `ubuntu debian`)
- Full `info()` dictionary
- Reads `/etc/os-release` and related sources

### Stack

- Python 3.14.6
- distro

### Architecture

`run.sh` -> `src/main.py` calls the `distro` accessors -> the library parses `/etc/os-release`, `lsb_release`, and distro-specific files -> normalized fields are printed.

### Note

`distro` targets Linux, where it reads `/etc/os-release` for a full distribution profile (`like`, `codename`, etc.). On macOS it falls back to `uname`, so `id`, `name`, and `version` are populated but `like` and `codename` are empty. Run it on a Linux host or inside a Linux container for a complete profile.

### Install

```bash
./install-deps.sh
```

### Run

```bash
./run.sh
```

### Output

```
id: ubuntu
name: Ubuntu 24.04.1 LTS
version: 24.04 (Noble Numbat)
major: 24
codename: Noble Numbat
like: debian
info: {'id': 'ubuntu', 'version': '24.04', 'version_parts': {'major': '24', 'minor': '04', 'build_number': ''}, 'like': 'debian', 'codename': 'Noble Numbat'}
```
