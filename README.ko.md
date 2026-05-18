# clap

[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | **한국어** | [日本語](README.ja.md) | [Español](README.es.md)

⚡️ Claude Code에서 DeepSeek, Anthropic, SiliconFlow를 원클릭으로 전환하세요!

Claude Code, Codex, Gemini CLI, OpenCode를 위한 초고속 TUI 프로필 & MCP 서버 관리자입니다. 더 이상 `.json`과 `.env` 파일을 수동으로 편집하지 마세요.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ 기능

- 🚀 **제로 설정 전환:** Claude Code, Gemini CLI 등에서 프로필을 즉시 전환합니다.
- 🐳 **17개 이상의 내장 제공자プリセット:** **DeepSeek V4**, Kimi, OpenRouter, SiliconFlow, AWS Bedrock, Azure, Groq, Together AI 등이 사전 설정되어 있습니다.
- 🔌 **실시간 MCP 관리:** Model Context Protocol 서버를 즉시 추가/제거하며 원자적 쓰기로 안전하게 저장합니다.
- 🛡️ **안전 최우선:** 백업되지 않은 자격 증명 덮어쓰기를 방지하는 스마트 활성화 경고.
- 🖱️ **터미널 마우스 지원:** 터미널 내에서 완전한 마우스 네비게이션, 클릭 및 스크롤.
- 🌐 **다국어 지원:** English, 简体中文, 繁體中文, 日本語 — 자동 감지 또는 한 줄 명령어로 전환.

## 설치

### npm으로

```bash
npm install -g @pterchan/clap
```

### curl로

```bash
curl -fsSL https://raw.githubusercontent.com/pterchan/Clap/main/install.sh | bash
```

또는 로컬에서:

```bash
./install.sh
```

## 사용법

```bash
clap                   # TUI 열기
clap ls                # 현재 도구의 프리셋 목록
clap use <name>        # 프리셋 활성화
clap current           # 현재 활성화된 프리셋 표시
clap backup <name>     # 현재 설정을 프리셋으로 저장
clap diff <name>       # 프리셋과 현재 설정 비교
clap backups           # 백업 목록
clap restore <name>    # 백업 복원
clap apps              # 지원하는 도구 목록
clap app <name>        # 기본 도구 전환 (claude/codex/gemini/opencode)
clap lang [code]       # 언어 표시/설정 (zh-CN, zh-TW, ja, en)
```

### 지원하는 도구

| 도구 | 설정 파일 | 형식 |
|-----|---------|------|
| Claude Code | `~/.claude/settings.json` | JSON |
| Codex | `~/.codex/auth.json` + `~/.codex/config.toml` | JSON + TOML |
| Gemini CLI | `~/.gemini/.env` | KEY=VALUE |
| OpenCode | `~/.config/opencode/opencode.json` | JSON |

### TUI 단축키

| 키 | 기능 | 키 | 기능 |
|----|------|----|------|
| `↑` / `↓` / `j` / `k` | 이동 | `Enter` | 활성화 |
| `e` | 편집 | `n` | 새로 만들기 |
| `d` | 복제 | `R` | 이름 바꾸기 |
| `D` | 삭제 | `/` | 필터 |
| `=` | 비교 | `b` | 백업 보기 |
| `r` | 새로고침 | `o` | 프리셋 폴더 열기 |
| `Tab` | 도구 전환 | `p` | 내장 프리셋 |
| `m` | MCP 관리 | `q` | 종료 |

### 마우스 지원

TUI에서 마우스를 사용할 수 있습니다:
- 탭（1행）을 **클릭**하여 도구 전환
- 프리셋 목록의 항목을 **클릭**하여 활성화
- 하단의 키 힌트를 **클릭**하여 해당 작업 실행（`e`、`n`、`d`、`D`、`/`、`=`、`b`、`r`、`o`、`p`、`m`、`q`）
- **스크롤**로 프리셋 목록 탐색

검색, 텍스트 입력 및 확인 프롬프트 중에는 실수로 인한 동작을 방지하기 위해 마우스 입력이 비활성화됩니다.

### 활성화 경고

프리셋을 활성화할 때, clap은 해당 인증 정보（API 키, 베이스 URL, 모델）를 저장된 모든 프리셋과 비교합니다:

- **경고 없음** — 현재 live config의 인증 정보가 이미 저장된 프리셋 중 하나에 포함되어 있는 경우（안전하게 전환 가능）.
- **부분 일치** — 동일한 제공자/베이스 URL이지만 다른 인증 정보（예: 다른 계정）. 현재 설정을 새 프리셋으로 먼저 저장할 것을 경고합니다.
- **일치 없음** — 베이스 URL과 API 키 모두 저장된 프리셋과 일치하지 않는 새로운 제공자. 현재 설정을 잃기 전에 저장할 것을 경고합니다.

`y`를 누르면 계속 진행하고, 다른 키를 누르면 취소합니다.

### 내장 제공자 프리셋

TUI에서 `p`를 눌러 17개 이상의 내장 제공자 프리셋을 탐색하세요:

- **Claude Code**: Anthropic 공식, DeepSeek, Kimi, SiliconFlow, OpenRouter, AWS Bedrock, Azure, Groq, Together AI
- **Codex**: OpenAI 공식, OpenRouter, DeepSeek
- **Gemini CLI**: Google 공식, OpenRouter
- **OpenCode**: Anthropic 공식, DeepSeek

하나를 선택하면 템플릿이 자동으로 채워집니다 — API 키만 입력하세요.

### MCP 관리

TUI에서 `m`을 눌러 (Claude Code 모드) MCP 서버를 관리하세요:
- `a` — 새 MCP 서버 추가 (이름 → 명령어 → 인수)
- `D` — 선택한 MCP 서버 삭제

변경 사항은 원자적 쓰기로 `~/.claude/settings.json`에 저장됩니다.
