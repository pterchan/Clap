# clap

**English** | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [Español](README.es.md)

⚡️ Switch between DeepSeek, Anthropic, and SiliconFlow in Claude Code with one click!

A lightning-fast TUI profile & MCP server manager for Claude Code, Codex, Gemini CLI, and OpenCode. Stop manually editing `.json` and `.env` files.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- 🚀 **Zero-Config Switching:** Instantly swap profiles for Claude Code, Gemini CLI, and more.
- 🐳 **Built-in 17+ Provider Presets:** Pre-charged setups for **DeepSeek V4**, Kimi, OpenRouter, SiliconFlow, AWS Bedrock, Azure, Groq, Together AI, and more.
- 🔌 **Live MCP Manager:** Add/remove Model Context Protocol servers on the fly with atomic writes.
- 🛡️ **Safety First:** Smart activation warnings to prevent overwriting un-backed-up credentials.
- 🖱️ **Terminal Mouse Support:** Full mouse navigation, clicking, and scrolling inside your terminal.
- 🌐 **Multi-language:** English, 简体中文, 繁體中文, 日本語 — auto-detected or one command to switch.

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
clap lang [code]       # show/set language (zh-CN, zh-TW, ja, en)
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

### Mouse Support

The TUI supports mouse interaction:
- **Click** a tab (row 1) to switch tools
- **Click** a preset in the list to activate it
- **Click** a key hint at the bottom to trigger the action (`e`, `n`, `d`, `D`, `/`, `=`, `b`, `r`, `o`, `p`, `m`, `q`)
- **Scroll** to navigate the preset list

Mouse input is disabled during search, text input, and confirmation prompts to prevent accidental actions.

### Activation Warnings

When activating a preset, clap compares its credentials (API key, base URL, model) against all stored presets:

- **Partial match** — Same provider or base URL but different credentials (e.g., different account). Prompts you to consider saving the current config as a new preset before switching.
- **No match** — Completely new provider with no matching base URL or API key in storage. Warns you to save the current config before losing it.

Press `y` to proceed or any other key to cancel.

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
