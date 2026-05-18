# clap

[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | **한국어** | [日本語](README.ja.md) | [Español](README.es.md)

clap은 Claude Code, Codex, Gemini CLI, OpenCode의 구성 프로필과 MCP 서버를 관리하는 터미널 사용자 인터페이스(TUI) 애플리케이션입니다. 공급자, 모델, 권한 설정은 각각 프리셋으로 저장되어 구성을 전환할 때 `.json` 및 `.env` 파일을 수동으로 편집할 필요가 없습니다.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 기능

- **프리셋 전환:** 도구별로 여러 구성 프리셋을 저장하고 TUI 또는 명령줄에서 원하는 프리셋을 활성화할 수 있습니다.
- **내장 제공자 프리셋:** 각 지원 도구의 공식 엔드포인트와 일반적인 호환 API 제공자를 위한 프리셋 템플릿을 포함하고 있습니다. 템플릿을 가져오면 편집 가능한 프리셋이 생성되며 API 키만 입력하면 됩니다.
- **MCP 서버 관리:** TUI에서 Model Context Protocol 서버를 추가하고 제거할 수 있으며, 모든 변경 사항은 원자적 쓰기로 저장됩니다.
- **활성화 경고:** 프리셋을 활성화하기 전에 현재 live config를 저장된 프리셋과 비교하며, 저장되지 않은 인증 정보가 어떤 프리셋에도 포함되지 않을 경우 경고가 표시됩니다.
- **마우스 지원:** TUI는 탭 전환, 항목 선택, 목록 스크롤에 마우스 입력을 받습니다. 검색, 텍스트 입력, 확인 프롬프트 중에는 마우스 입력이 비활성화됩니다.
- **다국어 지원:** English, 简体中文, 繁體中文, 日本語를 지원하며 자동 감지 또는 `clap lang` 명령으로 전환할 수 있습니다.

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

TUI에서 `p`를 누르면 내장 프리셋 템플릿을 탐색할 수 있습니다. 템플릿은 각 지원 도구의 공식 엔드포인트와 여러 호환 API 제공자를 다룹니다. 템플릿을 선택하면 프리셋 디렉터리로 복사되고 API 키를 입력할 편집기가 열립니다.

### MCP 관리

TUI에서 `m`을 눌러 (Claude Code 모드) MCP 서버를 관리하세요:
- `a` — 새 MCP 서버 추가 (이름 → 명령어 → 인수)
- `D` — 선택한 MCP 서버 삭제

변경 사항은 원자적 쓰기로 `~/.claude/settings.json`에 저장됩니다.
