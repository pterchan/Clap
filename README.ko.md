# clap

[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | **한국어** | [日本語](README.ja.md) | [Español](README.es.md)

멀티 도구 프로필 관리자 — Claude Code, Codex, Gemini CLI, OpenCode의 설정 프로필을 관리하는 경량 TUI 도구입니다.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

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
clap diff <name>       # 프리셋과 현재 설정 비교
clap backups           # 백업 목록
clap restore <name>    # 백업 복원
clap apps              # 지원하는 도구 목록
clap app <name>        # 기본 도구 전환 (claude/codex/gemini/opencode)
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
