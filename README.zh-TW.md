# clap

[English](README.md) | [简体中文](README.zh-CN.md) | **繁體中文** | [한국어](README.ko.md) | [日本語](README.ja.md) | [Español](README.es.md)

clap 是一個終端機使用者介面（TUI）程式，用於管理 Claude Code、Codex、Gemini CLI 與 OpenCode 的設定檔（profile）和 MCP 伺服器。每組供應商、模型與權限設定均以預設形式儲存，切換設定時無需手動編輯 `.json` 與 `.env` 檔案。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 特性

- **預設切換：** 可為每個工具儲存多個設定預設，並在 TUI 或命令列中啟用其中任意一個。
- **內建供應商預設：** 為各支援工具的官方端點及常見相容 API 供應商提供預設範本；匯入範本即產生可編輯的預設，只需填入 API key。
- **MCP 伺服器管理：** 可在 TUI 中新增和刪除 Model Context Protocol 伺服器項目，所有修改均以原子寫入方式儲存。
- **啟用警告：** 啟用預設前會將目前生效設定與已儲存預設進行比對；當未儲存的憑證不被任何預設覆蓋時顯示警告。
- **滑鼠支援：** TUI 接受滑鼠輸入，用於切換標籤頁、選擇項目和捲動清單；在搜尋、文字輸入和確認提示期間停用滑鼠輸入。
- **多語言介面：** English、简体中文、繁體中文、日本語，可自動偵測或透過 `clap lang` 命令切換。

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
clap backup <name>     # 將目前設定儲存為預設
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

在 TUI 中按 `p` 可瀏覽內建預設範本。範本涵蓋各支援工具的官方端點及若干相容 API 供應商。選擇範本後，該範本會被複製到預設目錄並開啟編輯器，用於填入 API key。

### MCP 管理

在 TUI 中按 `m`（Claude Code 模式）管理 MCP 伺服器：
- `a` — 新增 MCP 伺服器（名稱 → 指令 → 參數）
- `D` — 刪除選中的 MCP 伺服器

修改以原子寫入方式儲存至 `~/.claude/settings.json`。
