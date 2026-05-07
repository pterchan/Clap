# clap

[English](README.md) | **简体中文** | [繁體中文](README.zh-TW.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [Español](README.es.md)

Claude Code 配置管理器 —— 一个在终端里管理多份 `settings.json` 配置文件的 TUI 工具。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 安装

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
clap ls                # 列出预设
clap use <name>        # 激活预设
clap current           # 显示当前激活的预设
clap diff <name>       # 对比预设与当前配置
clap backups           # 列出备份
clap restore <name>    # 恢复备份
```

### TUI 快捷键

| 按键 | 功能 | 按键 | 功能 |
|------|------|------|------|
| `↑` / `↓` / `j` / `k` | 移动 | `Enter` | 激活 |
| `e` | 编辑 | `n` | 新建 |
| `d` | 复制 | `R` | 重命名 |
| `D` | 删除 | `/` | 筛选 |
| `=` | 对比 | `b` | 查看备份 |
| `r` | 刷新 | `o` | 在 Finder 中打开 |
| `q` | 退出 | | |
