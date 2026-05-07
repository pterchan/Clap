# clap

**English** | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [Español](README.es.md)

Claude Code Profile Manager — A TUI tool for managing multiple `settings.json` profiles.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Install

### via npm

```bash
npm install -g @pterchan/clap
```

### via curl

```bash
curl -fsSL https://raw.githubusercontent.com/pterchan/Clap/main/install.sh | bash
```

Or locally:

```bash
./install.sh
```

## Usage

```bash
clap                   # open TUI
clap ls                # list presets
clap use <name>        # activate
clap current           # show active
clap diff <name>       # compare preset with current settings
clap backups           # list backups
clap restore <name>    # restore a backup
```

### TUI Keybindings

| Key | Function | Key | Function |
|-----|----------|-----|----------|
| `↑` / `↓` / `j` / `k` | Move | `Enter` | Activate |
| `e` | Edit | `n` | New |
| `d` | Duplicate | `R` | Rename |
| `D` | Delete | `/` | Filter |
| `=` | Diff | `b` | View Backups |
| `r` | Reload | `o` | Open in Finder |
| `q` | Quit | | |
