# clap

[English](README.md) | [简体中文](README.zh-CN.md) | **繁體中文** | [한국어](README.ko.md) | [日本語](README.ja.md) | [Español](README.es.md)

⚡️ 在 Claude Code 中一鍵切換 DeepSeek、Anthropic、矽基流動！

輕量級光速 TUI 設定 & MCP 伺服器管理器，支援 Claude Code、Codex、Gemini CLI 和 OpenCode。告別手動編輯 `.json` 和 `.env` 檔案。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ 特性

- 🚀 **零設定切換：** 一鍵在 Claude Code、Gemini CLI 等多個工具間切換設定。
- 🐳 **內建 17+ 供應商預設：** 預先配置了 **DeepSeek V4**、Kimi、OpenRouter、矽基流動、AWS Bedrock、Azure、Groq、Together AI 等。
- 🔌 **即時 MCP 管理：** 隨時新增/刪除 Model Context Protocol 伺服器，原子寫入保障安全。
- 🛡️ **安全優先：** 智慧啟用警告，防止覆蓋未備份的憑據。
- 🖱️ **終端機滑鼠支援：** 終端機內完整滑鼠導覽、點擊和捲動。
- 🌐 **多語言：** English, 简体中文, 繁體中文, 日本語 — 自動偵測或一鍵切換。

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
clap lang [code]       # 顯示/設定語言（zh-CN, zh-TW, ja, en）
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

### 滑鼠支援

TUI 支援滑鼠操作：
- **點擊** Tab 標籤（第 1 行）切換工具
- **點擊** 預設列表中的項目來啟用
- **點擊** 底部的快捷鍵標籤觸發對應操作（`e`、`n`、`d`、`D`、`/`、`=`、`b`、`r`、`o`、`p`、`m`、`q`）
- **滾輪** 滾動預設列表

在搜尋、文字輸入和確認提示期間，滑鼠輸入會被禁用，以防止誤操作。

### 啟用警告

啟用預設時，clap 會將其憑證（API key、Base URL、模型）與所有已儲存的預設進行比對：

- **無需警告** — 目前 live config 的憑證已被任意一個已儲存的預設覆蓋（可安全切換）。
- **部分匹配** — 相同的供應商或 Base URL，但憑證不同（例如不同帳戶）。提醒你考慮先將目前設定儲存為新預設。
- **無匹配** — 全新的供應商，Base URL 和 API key 均不匹配。提醒你在遺失前儲存目前設定。

按 `y` 繼續，其他鍵取消。

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
