# clap

[English](README.md) | **简体中文** | [繁體中文](README.zh-TW.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [Español](README.es.md)

多工具配置管理器 —— 一个轻量级 TUI 工具，管理 Claude Code、Codex、Gemini CLI 和 OpenCode 的配置文件。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

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
