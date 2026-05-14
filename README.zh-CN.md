# clap

[English](README.md) | **简体中文** | [繁體中文](README.zh-TW.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [Español](README.es.md)

⚡️ 在 Claude Code 中一键切换 DeepSeek、Anthropic、硅基流动！

轻量级光速 TUI 配置 & MCP 服务器管理器，支持 Claude Code、Codex、Gemini CLI 和 OpenCode。告别手动编辑 `.json` 和 `.env` 文件。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ 特性

- 🚀 **零配置切换：** 一键在 Claude Code、Gemini CLI 等多个工具间切换配置。
- 🐳 **内置 17+ 供应商预设：** 预配置了 **DeepSeek V4**、Kimi、OpenRouter、硅基流动、AWS Bedrock、Azure、Groq、Together AI 等。
- 🔌 **实时 MCP 管理：** 随时添加/删除 Model Context Protocol 服务器，原子写入保障安全。
- 🛡️ **安全优先：** 智能激活警告，防止覆盖未备份的凭据。
- 🖱️ **终端鼠标支持：** 终端内完整鼠标导航、点击和滚动。
- 🌐 **多语言：** English, 简体中文, 繁體中文, 日本語 — 自动检测或一键切换。

## 安装

### 通过 npm

```bash
npm install -g @pterchan/clap
```

### 通过 curl

```bash
curl -fsSL https://raw.githubusercontent.com/pterchan/Clap/main/install.sh | bash
```

或者本地安装：

```bash
./install.sh
```

## 用法

```bash
clap                   # 打开 TUI
clap ls                # 列出当前工具的预设
clap use <name>        # 激活预设
clap current           # 显示当前激活的预设
clap diff <name>       # 对比预设与当前配置
clap backups           # 列出备份
clap restore <name>    # 恢复备份
clap apps              # 列出支持的工具
clap app <name>        # 切换默认工具（claude/codex/gemini/opencode）
clap lang [code]       # 显示/设置语言（zh-CN, zh-TW, ja, en）
```

### 支持的工具

| 工具 | 配置文件 | 格式 |
|-----|---------|------|
| Claude Code | `~/.claude/settings.json` | JSON |
| Codex | `~/.codex/auth.json` + `~/.codex/config.toml` | JSON + TOML |
| Gemini CLI | `~/.gemini/.env` | KEY=VALUE |
| OpenCode | `~/.config/opencode/opencode.json` | JSON |

### TUI 快捷键

| 按键 | 功能 | 按键 | 功能 |
|------|------|------|------|
| `↑` / `↓` / `j` / `k` | 移动 | `Enter` | 激活 |
| `e` | 编辑 | `n` | 新建 |
| `d` | 复制 | `R` | 重命名 |
| `D` | 删除 | `/` | 筛选 |
| `=` | 对比 | `b` | 查看备份 |
| `r` | 刷新 | `o` | 打开预设文件夹 |
| `Tab` | 切换工具 | `p` | 内置预设库 |
| `m` | MCP 管理 | `q` | 退出 |

### 鼠标支持

TUI 支持鼠标操作：
- **点击** Tab 标签（第 1 行）切换工具
- **点击** 预设列表中的项目来激活
- **点击** 底部的快捷键标签触发对应操作（`e`、`n`、`d`、`D`、`/`、`=`、`b`、`r`、`o`、`p`、`m`、`q`）
- **滚轮** 滚动预设列表

在搜索、文本输入和确认提示期间，鼠标输入会被禁用，以防止误操作。

### 激活警告

激活预设时，clap 会将其凭据（API key、Base URL、模型）与所有已存储的预设进行比对：

- **无需警告** — 当前 live config 的凭据已被任意一个已存储的预设覆盖（可安全切换）。
- **部分匹配** — 相同的供应商或 Base URL，但凭据不同（例如不同账户）。提醒你考虑先将当前配置保存为新预设。
- **无匹配** — 全新的供应商，Base URL 和 API key 均不匹配。提醒你在丢失前保存当前配置。

按 `y` 继续，其他键取消。

### 内置供应商预设

在 TUI 中按 `p` 浏览 17+ 个内置供应商预设，包括：

- **Claude Code**: Anthropic 官方、DeepSeek、Kimi、硅基流动、OpenRouter、AWS Bedrock、Azure、Groq、Together AI
- **Codex**: OpenAI 官方、OpenRouter、DeepSeek
- **Gemini CLI**: Google 官方、OpenRouter
- **OpenCode**: Anthropic 官方、DeepSeek

选择一个即可自动填充模板——只需填入 API key。

### MCP 管理

在 TUI 中按 `m`（Claude Code 模式）管理 MCP 服务器：
- `a` — 添加 MCP 服务器（名称 → 命令 → 参数）
- `D` — 删除选中的 MCP 服务器

修改以原子写入方式保存至 `~/.claude/settings.json`。
