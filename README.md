# clap

**English** | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [Español](README.es.md)

Multi-Tool Profile Manager — A lightweight TUI tool for managing config profiles across Claude Code, Codex, Gemini CLI, and OpenCode.

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
clap ls                # list presets for current app
clap use <name>        # activate a preset
clap current           # show active preset name
clap diff <name>       # diff preset against current settings
clap backups           # list backups
clap restore <name>    # restore a backup
clap apps              # list supported tools
clap app <name>        # switch default app (claude/codex/gemini/opencode)
```

### Supported Tools

| App | Config File(s) | Format |
|-----|---------------|--------|
| Claude Code | `~/.claude/settings.json` | JSON |
| Codex | `~/.codex/auth.json` + `~/.codex/config.toml` | JSON + TOML |
| Gemini CLI | `~/.gemini/.env` | KEY=VALUE |
| OpenCode | `~/.config/opencode/opencode.json` | JSON |

### TUI Keybindings

| Key | Function | Key | Function |
|-----|----------|-----|----------|
| `↑` / `↓` / `j` / `k` | Move | `Enter` | Activate |
| `e` | Edit | `n` | New |
| `d` | Duplicate | `R` | Rename |
| `D` | Delete | `/` | Filter |
| `=` | Diff | `b` | View Backups |
| `r` | Reload | `o` | Open Presets Dir |
| `Tab` | Switch Tool | `p` | Built-in Presets |
| `m` | MCP Manager | `q` | Quit |

### Built-in Provider Presets

Press `p` in TUI to browse 17+ built-in provider presets, including:

- **Claude Code**: Anthropic official, DeepSeek, Kimi, SiliconFlow, OpenRouter, AWS Bedrock, Azure, Groq, Together AI
- **Codex**: OpenAI official, OpenRouter, DeepSeek
- **Gemini CLI**: Google official, OpenRouter
- **OpenCode**: Anthropic official, DeepSeek

Select one to auto-fill the template — just add your API key.

### MCP Management

Press `m` in TUI (Claude Code mode) to manage MCP servers:
- `a` — Add a new MCP server (name → command → args)
- `D` — Delete the selected MCP server

Changes are written to `~/.claude/settings.json` with atomic writes.
