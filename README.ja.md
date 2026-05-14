# clap

[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [한국어](README.ko.md) | **日本語** | [Español](README.es.md)

⚡️ Claude Code で DeepSeek、Anthropic、SiliconFlow をワンクリックで切り替え！

Claude Code、Codex、Gemini CLI、OpenCode 向けの高速 TUI プロファイル & MCP サーバーマネージャー。`.json` や `.env` ファイルの手動編集はもう不要です。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ 特徴

- 🚀 **ゼロ設定切替：** Claude Code、Gemini CLI などのプロファイルを瞬時に切り替え。
- 🐳 **17以上の内蔵プロバイダープリセット：** **DeepSeek V4**、Kimi、OpenRouter、SiliconFlow、AWS Bedrock、Azure、Groq、Together AI などをプリセット済み。
- 🔌 **ライブ MCP 管理：** Model Context Protocol サーバーをアトミック書き込みでその場で追加/削除。
- 🛡️ **安全第一：** 未バックアップの認証情報の上書きを防ぐスマートな有効化警告。
- 🖱️ **端末マウスサポート：** 端末内での完全なマウスナビゲーション、クリック、スクロール。
- 🌐 **多言語対応：** English, 简体中文, 繁體中文, 日本語 — 自動検出またはワンコマンドで切替。

## インストール

### npm 経由

```bash
npm install -g @pterchan/clap
```

### curl 経由

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
clap ls                # 現在のツールのプリセット一覧
clap use <name>        # プリセットを有効化
clap current           # 現在のプリセットを表示
clap diff <name>       # プリセットと現在の設定を比較
clap backups           # バックアップ一覧
clap restore <name>    # バックアップを復元
clap apps              # 対応ツール一覧
clap app <name>        # デフォルトツールを切替（claude/codex/gemini/opencode）
clap lang [code]       # 言語の表示/設定（zh-CN, zh-TW, ja, en）
```

### 対応ツール

| ツール | 設定ファイル | 形式 |
|-----|---------|------|
| Claude Code | `~/.claude/settings.json` | JSON |
| Codex | `~/.codex/auth.json` + `~/.codex/config.toml` | JSON + TOML |
| Gemini CLI | `~/.gemini/.env` | KEY=VALUE |
| OpenCode | `~/.config/opencode/opencode.json` | JSON |

### TUI キーバインド

| キー | 機能 | キー | 機能 |
|------|------|------|------|
| `↑` / `↓` / `j` / `k` | 移動 | `Enter` | 有効化 |
| `e` | 編集 | `n` | 新規作成 |
| `d` | 複製 | `R` | 名前を変更 |
| `D` | 削除 | `/` | フィルタ |
| `=` | 比較 | `b` | バックアップを表示 |
| `r` | 再読み込み | `o` | プリセットフォルダを開く |
| `Tab` | ツール切替 | `p` | 内蔵プリセット |
| `m` | MCP 管理 | `q` | 終了 |

### マウスサポート

TUI はマウス操作に対応しています：
- タブ（1 行目）を**クリック**してツールを切り替え
- プリセット一覧の項目を**クリック**して有効化
- 下部のキーヒントを**クリック**して対応する操作を実行（`e`、`n`、`d`、`D`、`/`、`=`、`b`、`r`、`o`、`p`、`m`、`q`）
- **スクロール**でプリセット一覧を移動

検索中、テキスト入力中、確認プロンプト表示中は、誤操作を防ぐためにマウス入力は無効になります。

### 有効化時の警告

プリセットを有効化する際、clap はその認証情報（API キー、ベース URL、モデル）を保存済みの全プリセットと比較します：

- **警告なし** — 現在の live config の認証情報がいずれかの保存済みプリセットでカバーされている場合（安全に切り替え可能）。
- **部分一致** — 同じプロバイダー/ベース URL だが異なる認証情報（別アカウントなど）。現在の設定を新しいプリセットとして保存するよう警告します。
- **一致なし** — ベース URL も API キーも保存済みプリセットと一致しない新しいプロバイダー。現在の設定を失う前に保存するよう警告します。

`y` で続行、他のキーでキャンセルします。

### 内蔵プロバイダープリセット

TUI で `p` を押して 17 以上の内蔵プロバイダープリセットを参照：

- **Claude Code**: Anthropic 公式、DeepSeek、Kimi、SiliconFlow、OpenRouter、AWS Bedrock、Azure、Groq、Together AI
- **Codex**: OpenAI 公式、OpenRouter、DeepSeek
- **Gemini CLI**: Google 公式、OpenRouter
- **OpenCode**: Anthropic 公式、DeepSeek

選択するだけでテンプレートが自動入力されます — API キーを入力するだけです。

### MCP 管理

TUI で `m` を押して（Claude Code モード）MCP サーバーを管理：
- `a` — 新しい MCP サーバーを追加（名前 → コマンド → 引数）
- `D` — 選択した MCP サーバーを削除

変更はアトミック書き込みで `~/.claude/settings.json` に保存されます。
