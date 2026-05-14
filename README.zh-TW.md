# clap

[English](README.md) | [简体中文](README.zh-CN.md) | **繁體中文** | [한국어](README.ko.md) | [日本語](README.ja.md) | [Español](README.es.md)

多工具設定管理器 —— 一個輕量級 TUI 工具，管理 Claude Code、Codex、Gemini CLI 和 OpenCode 的設定檔。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 安裝

### 透過 npm

```bash
npm install -g @pterchan/clap
```

### 透過 curl

```bash
curl -fsSL https://raw.githubusercontent.com/pterchan/Clap/main/install.sh | bash
```

或者在本機安裝：

```bash
./install.sh
```

## 用法

```bash
clap                   # 開啟 TUI
clap ls                # 列出目前工具的預設
clap use <name>        # 啟用預設
clap current           # 顯示目前啟用的預設
clap diff <name>       # 比對預設與目前設定
clap backups           # 列出備份
clap restore <name>    # 復原備份
clap apps              # 列出支援的工具
clap app <name>        # 切換預設工具（claude/codex/gemini/opencode）
```

### 支援的工具

| 工具 | 設定檔 | 格式 |
|-----|---------|------|
| Claude Code | `~/.claude/settings.json` | JSON |
| Codex | `~/.codex/auth.json` + `~/.codex/config.toml` | JSON + TOML |
| Gemini CLI | `~/.gemini/.env` | KEY=VALUE |
| OpenCode | `~/.config/opencode/opencode.json` | JSON |

### TUI 快捷鍵

| 按鍵 | 功能 | 按鍵 | 功能 |
|------|------|------|------|
| `↑` / `↓` / `j` / `k` | 移動 | `Enter` | 啟用 |
| `e` | 編輯 | `n` | 新增 |
| `d` | 複製 | `R` | 重新命名 |
| `D` | 刪除 | `/` | 篩選 |
| `=` | 比對 | `b` | 查看備份 |
| `r` | 重新整理 | `o` | 開啟預設資料夾 |
| `Tab` | 切換工具 | `p` | 內建預設庫 |
| `m` | MCP 管理 | `q` | 離開 |

### 內建供應商預設

在 TUI 中按 `p` 瀏覽 17+ 個內建供應商預設，包括：

- **Claude Code**: Anthropic 官方、DeepSeek、Kimi、矽基流動、OpenRouter、AWS Bedrock、Azure、Groq、Together AI
- **Codex**: OpenAI 官方、OpenRouter、DeepSeek
- **Gemini CLI**: Google 官方、OpenRouter
- **OpenCode**: Anthropic 官方、DeepSeek

選擇一個即可自動填入範本——只需填入 API key。

### MCP 管理

在 TUI 中按 `m`（Claude Code 模式）管理 MCP 伺服器：
- `a` — 新增 MCP 伺服器（名稱 → 指令 → 參數）
- `D` — 刪除選中的 MCP 伺服器

修改以原子寫入方式儲存至 `~/.claude/settings.json`。
