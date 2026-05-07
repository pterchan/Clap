# clap

[English](README.md) | [简体中文](README.zh-CN.md) | **繁體中文** | [한국어](README.ko.md) | [日本語](README.ja.md) | [Español](README.es.md)

Claude Code 設定管理器 —— 一個在終端機裡管理多份 `settings.json` 設定檔的 TUI 工具。

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
clap ls                # 列出預設
clap use <name>        # 啟用預設
clap current           # 顯示目前啟用的預設
clap diff <name>       # 比對預設與目前設定
clap backups           # 列出備份
clap restore <name>    # 恢復備份
```

### TUI 快捷鍵

| 按鍵 | 功能 | 按鍵 | 功能 |
|------|------|------|------|
| `↑` / `↓` / `j` / `k` | 移動 | `Enter` | 啟用 |
| `e` | 編輯 | `n` | 新增 |
| `d` | 複製 | `R` | 重新命名 |
| `D` | 刪除 | `/` | 篩選 |
| `=` | 比對 | `b` | 查看備份 |
| `r` | 重新整理 | `o` | 在 Finder 中開啟 |
| `q` | 離開 | | |
