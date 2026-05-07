# clap

[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [한국어](README.ko.md) | **日本語** | [Español](README.es.md)

Claude Code プロファイルマネージャー — ターミナル上で複数の `settings.json` プロファイルを管理する TUI ツールです。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## インストール

```bash
curl -fsSL https://raw.githubusercontent.com/pterchan/Clap/main/install.sh | bash
```

またはローカルで:

```bash
./install.sh
```

## 使い方

```bash
clap                   # TUI を開く
clap ls                # プリセット一覧
clap use <name>        # プリセットを有効化
clap current           # 現在のプリセットを表示
clap diff <name>       # プリセットと現在の設定を比較
clap backups           # バックアップ一覧
clap restore <name>    # バックアップを復元
```

### TUI キーバインド

| キー | 機能 | キー | 機能 |
|------|------|------|------|
| `↑` / `↓` / `j` / `k` | 移動 | `Enter` | 有効化 |
| `e` | 編集 | `n` | 新規作成 |
| `d` | 複製 | `R` | 名前を変更 |
| `D` | 削除 | `/` | フィルタ |
| `=` | 比較 | `b` | バックアップを表示 |
| `r` | 再読み込み | `o` | Finder で開く |
| `q` | 終了 | | |
