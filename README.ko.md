# clap

[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | **한국어** | [日本語](README.ja.md) | [Español](README.es.md)

Claude Code 프로필 관리자 — 터미널에서 여러 `settings.json` 프로필을 관리하는 TUI 도구입니다.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 설치

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
clap ls                # 프리셋 목록
clap use <name>        # 프리셋 활성화
clap current           # 현재 활성화된 프리셋 표시
clap diff <name>       # 프리셋과 현재 설정 비교
clap backups           # 백업 목록
clap restore <name>    # 백업 복원
```

### TUI 단축키

| 키 | 기능 | 키 | 기능 |
|----|------|----|------|
| `↑` / `↓` / `j` / `k` | 이동 | `Enter` | 활성화 |
| `e` | 편집 | `n` | 새로 만들기 |
| `d` | 복제 | `R` | 이름 바꾸기 |
| `D` | 삭제 | `/` | 필터 |
| `=` | 비교 | `b` | 백업 보기 |
| `r` | 새로고침 | `o` | Finder에서 열기 |
| `q` | 종료 | | |
