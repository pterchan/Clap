#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 pterchan
"""
clap v2 — Multi-Tool Profile Manager (TUI)
Manage settings.json profiles for Claude Code, Codex, Gemini CLI, and OpenCode.
"""
import difflib
import json
import os
import re
import shutil
import subprocess
import sys
import shlex
import tempfile
from pathlib import Path
from datetime import datetime

VERSION = "0.2.0"

HOME = Path.home()
CLAP_DIR = HOME / ".clap"

MIN_H = 12
MIN_W = 70
LABEL_WIDTH = 14
MIN_LIST_W = 28
MAX_BACKUPS = 30

MODE_NEW = "new"
MODE_DUP = "dup"
MODE_RENAME = "rename"


# ── AppConfig ──────────────────────────────────────────────────────────

class AppConfig:
    __slots__ = ('name', 'label', 'settings_file', 'settings_file2',
                 'presets_dir', 'backup_dir', 'active_file', 'fmt', 'fmt2',
                 'default_template', 'examples')

    def __init__(self, name, label, settings_file, presets_dir,
                 backup_dir, active_file, fmt, default_template=None,
                 examples=None, settings_file2=None, fmt2=None):
        self.name = name
        self.label = label
        self.settings_file = settings_file
        self.settings_file2 = settings_file2
        self.presets_dir = presets_dir
        self.backup_dir = backup_dir
        self.active_file = active_file
        self.fmt = fmt
        self.fmt2 = fmt2
        self.default_template = default_template or {}
        self.examples = examples or {}


def _build_apps():
    """Return AppConfig dict for all supported CLI tools."""
    base = CLAP_DIR
    claude_default = {
        "env": {
            "ANTHROPIC_API_KEY": "sk-...",
            "ANTHROPIC_BASE_URL": "https://api.anthropic.com",
            "ANTHROPIC_MODEL": "claude-sonnet-4-6",
            "CLAUDE_CODE_MAX_OUTPUT_TOKENS": "32000"
        },
        "permissions": {
            "defaultMode": "default",
            "allow": [],
            "deny": []
        }
    }
    claude_examples = {
        "anthropic-official": {
            "env": {
                "ANTHROPIC_API_KEY": "sk-ant-xxxxx",
                "ANTHROPIC_MODEL": "claude-sonnet-4-6",
                "CLAUDE_CODE_MAX_OUTPUT_TOKENS": "32000"
            },
            "permissions": {
                "defaultMode": "default",
                "allow": ["Bash(git:*)", "Read", "Edit", "Write"],
                "deny": ["Bash(rm -rf:*)", "Bash(sudo:*)"]
            }
        },
        "deepseek-proxy": {
            "env": {
                "ANTHROPIC_API_KEY": "sk-deepseek-xxxxx",
                "ANTHROPIC_BASE_URL": "https://api.deepseek.com/anthropic",
                "ANTHROPIC_MODEL": "deepseek-chat",
                "CLAUDE_CODE_MAX_OUTPUT_TOKENS": "8000"
            },
            "permissions": {
                "defaultMode": "acceptEdits",
                "allow": ["Read", "Edit", "Write", "Bash"],
                "deny": []
            }
        },
        "kimi-readonly": {
            "env": {
                "ANTHROPIC_AUTH_TOKEN": "sk-kimi-xxxxx",
                "ANTHROPIC_BASE_URL": "https://api.moonshot.cn/anthropic",
                "ANTHROPIC_MODEL": "kimi-k2.6"
            },
            "permissions": {
                "defaultMode": "plan",
                "allow": ["Read", "Glob", "Grep"],
                "deny": ["Write", "Edit", "Bash"]
            }
        }
    }
    gemini_default = {
        "GEMINI_API_KEY": "sk-...",
        "GOOGLE_GEMINI_BASE_URL": "https://generativelanguage.googleapis.com/v1beta/models",
        "GEMINI_MODEL": "gemini-2.0-flash"
    }
    gemini_examples = {
        "gemini-official": {
            "GEMINI_API_KEY": "your-gemini-api-key",
            "GOOGLE_GEMINI_BASE_URL": "https://generativelanguage.googleapis.com/v1beta/models",
            "GEMINI_MODEL": "gemini-2.0-flash"
        }
    }
    codex_default = {
        "auth": {"OPENAI_API_KEY": "sk-..."},
        "config": {"model": "gpt-5", "model_provider": "openai",
                    "model_reasoning_effort": "high"}
    }
    codex_examples = {
        "codex-official": {
            "auth": {"OPENAI_API_KEY": "your-openai-key"},
            "config": {"model": "gpt-5", "model_provider": "openai",
                        "model_reasoning_effort": "high"}
        }
    }
    opencode_default = {
        "providers": {
            "anthropic": {
                "api_key": "sk-...",
                "base_url": "https://api.anthropic.com",
                "model": "claude-sonnet-4-6"
            }
        }
    }
    opencode_examples = {
        "opencode-anthropic": {
            "providers": {
                "anthropic": {
                    "api_key": "your-anthropic-key",
                    "base_url": "https://api.anthropic.com",
                    "model": "claude-sonnet-4-6"
                }
            }
        }
    }
    return {
        "claude": AppConfig(
            name="claude", label="Claude Code",
            settings_file=HOME / ".claude/settings.json",
            presets_dir=base / "presets",
            backup_dir=base / "backups",
            active_file=base / "active",
            fmt="json",
            default_template=claude_default,
            examples=claude_examples,
        ),
        "codex": AppConfig(
            name="codex", label="Codex",
            settings_file=HOME / ".codex/auth.json",
            settings_file2=HOME / ".codex/config.toml",
            presets_dir=base / "presets-codex",
            backup_dir=base / "backups-codex",
            active_file=base / "active-codex",
            fmt="json", fmt2="toml",
            default_template=codex_default,
            examples=codex_examples,
        ),
        "gemini": AppConfig(
            name="gemini", label="Gemini CLI",
            settings_file=HOME / ".gemini/.env",
            presets_dir=base / "presets-gemini",
            backup_dir=base / "backups-gemini",
            active_file=base / "active-gemini",
            fmt="env",
            default_template=gemini_default,
            examples=gemini_examples,
        ),
        "opencode": AppConfig(
            name="opencode", label="OpenCode",
            settings_file=HOME / ".config/opencode/opencode.json",
            presets_dir=base / "presets-opencode",
            backup_dir=base / "backups-opencode",
            active_file=base / "active-opencode",
            fmt="json5",
            default_template=opencode_default,
            examples=opencode_examples,
        ),
    }


DEFAULT_APP_FILE = CLAP_DIR / "default-app"

APPS: dict = {}
_cur_app_name: str = "claude"
APP_ORDER = ["claude", "codex", "gemini", "opencode"]


def _load_default_app():
    """Load persisted default app name, or 'claude'."""
    global _cur_app_name
    try:
        if DEFAULT_APP_FILE.exists():
            name = DEFAULT_APP_FILE.read_text().strip()
            if name in APP_ORDER:
                _cur_app_name = name
    except Exception:
        pass


def _app():
    return APPS[_cur_app_name]


# ── Built-in Provider Presets ──────────────────────────────────────────

BUILTIN_PROVIDERS = {
    "claude": {
        "Official": [
            {"name": "anthropic-official",
             "env": {"ANTHROPIC_API_KEY": "",
                     "ANTHROPIC_MODEL": "claude-opus-4-5",
                     "CLAUDE_CODE_MAX_OUTPUT_TOKENS": "32000"},
             "permissions": {"defaultMode": "default", "allow": [], "deny": []}},
        ],
        "Relay-CN": [
            {"name": "deepseek",
             "env": {"ANTHROPIC_API_KEY": "",
                     "ANTHROPIC_BASE_URL": "https://api.deepseek.com/anthropic",
                     "ANTHROPIC_MODEL": "deepseek-chat"}},
            {"name": "kimi",
             "env": {"ANTHROPIC_AUTH_TOKEN": "",
                     "ANTHROPIC_BASE_URL": "https://api.moonshot.cn/anthropic",
                     "ANTHROPIC_MODEL": "kimi-k2.6"}},
            {"name": "siliconflow",
             "env": {"ANTHROPIC_API_KEY": "",
                     "ANTHROPIC_BASE_URL": "https://api.siliconflow.cn/v1/anthropic",
                     "ANTHROPIC_MODEL": "deepseek-v3"}},
            {"name": "openrouter",
             "env": {"ANTHROPIC_API_KEY": "",
                     "ANTHROPIC_BASE_URL": "https://openrouter.ai/api/v1/anthropic",
                     "ANTHROPIC_MODEL": ""}},
            {"name": "packyapi",
             "env": {"ANTHROPIC_AUTH_TOKEN": "",
                     "ANTHROPIC_BASE_URL": "https://api.packyapi.com/v1/anthropic",
                     "ANTHROPIC_MODEL": ""}},
        ],
        "Cloud": [
            {"name": "aws-bedrock",
             "env": {"ANTHROPIC_API_KEY": "",
                     "ANTHROPIC_BASE_URL": "https://bedrock-runtime.us-east-1.amazonaws.com",
                     "ANTHROPIC_MODEL": "us.anthropic.claude-3-5-sonnet-20241022-v2:0"}},
            {"name": "azure-openai",
             "env": {"ANTHROPIC_AUTH_TOKEN": "",
                     "ANTHROPIC_BASE_URL": "https://your-resource.openai.azure.com/anthropic",
                     "ANTHROPIC_MODEL": "azure-claude"}},
        ],
        "International": [
            {"name": "groq",
             "env": {"ANTHROPIC_API_KEY": "",
                     "ANTHROPIC_BASE_URL": "https://api.groq.com/openai/v1/anthropic",
                     "ANTHROPIC_MODEL": "deepseek-r1-distill-llama-70b"}},
            {"name": "together-ai",
             "env": {"ANTHROPIC_API_KEY": "",
                     "ANTHROPIC_BASE_URL": "https://api.together.xyz/v1/anthropic",
                     "ANTHROPIC_MODEL": "deepseek-v3"}},
        ],
    },
    "gemini": {
        "Official": [
            {"name": "gemini-official",
             "GEMINI_API_KEY": "",
             "GOOGLE_GEMINI_BASE_URL": "https://generativelanguage.googleapis.com/v1beta/models",
             "GEMINI_MODEL": "gemini-2.0-flash"},
        ],
        "Relay": [
            {"name": "openrouter-gemini",
             "GEMINI_API_KEY": "",
             "GOOGLE_GEMINI_BASE_URL": "https://openrouter.ai/api/v1/google",
             "GEMINI_MODEL": "gemini-2.0-flash"},
        ],
    },
    "codex": {
        "Official": [
            {"name": "codex-official",
             "auth": {"OPENAI_API_KEY": ""},
             "config": {"model": "gpt-5", "model_provider": "openai",
                         "model_reasoning_effort": "high"}},
        ],
        "Relay": [
            {"name": "openrouter-codex",
             "auth": {"OPENAI_API_KEY": ""},
             "config": {"model": "openai/gpt-5",
                         "model_provider": "open-router",
                         "base_url": "https://openrouter.ai/api/v1"}},
            {"name": "deepseek-codex",
             "auth": {"OPENAI_API_KEY": ""},
             "config": {"model": "deepseek-chat",
                         "model_provider": "deepseek",
                         "base_url": "https://api.deepseek.com/v1"}},
        ],
    },
    "opencode": {
        "Official": [
            {"name": "opencode-anthropic",
             "providers": {"anthropic": {"api_key": "",
                                          "base_url": "https://api.anthropic.com",
                                          "model": "claude-sonnet-4-6"}}},
        ],
        "Relay": [
            {"name": "opencode-deepseek",
             "providers": {"deepseek": {"api_key": "",
                                         "base_url": "https://api.deepseek.com/v1",
                                         "model": "deepseek-chat"}}},
        ],
    },
}


# ── File I/O utils ─────────────────────────────────────────────────────

def _chmod600(path):
    try:
        os.chmod(path, 0o600)
    except Exception as e:
        print(f"Warning: could not chmod 600 {path}: {e}", file=sys.stderr)


def _atomic_write(dest, content):
    """Write content to dest atomically: tmp file + rename."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=dest.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(content)
        os.chmod(tmp, 0o600)
        Path(tmp).replace(dest)
    except Exception:
        try:
            os.unlink(tmp)
        except Exception:
            pass
        raise


def _read_env_file(path):
    """Read KEY=VALUE file, ignoring comments and blank lines."""
    result = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        k, _, v = line.partition('=')
        result[k.strip()] = v.strip()
    return result


def _write_env_file(path, data):
    """Write dict as KEY=VALUE lines."""
    lines = [f"{k}={v}\n" for k, v in data.items()]
    _atomic_write(path, "".join(lines))


def _read_toml_simple(path):
    """Read a minimal TOML subset: [section] + key = "value"."""
    result = {}
    section = None
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('[') and line.endswith(']'):
            section = line[1:-1].strip()
            result.setdefault(section, {})
        elif '=' in line:
            k, _, v = line.partition('=')
            k, v = k.strip(), v.strip().strip('"').strip("'")
            target = result[section] if section else result
            target[k] = v
    return result


def _write_toml_simple(path, data):
    """Write {section: {k:v}} or {k:v} as minimal TOML."""
    lines = []
    flat = {k: v for k, v in data.items() if not isinstance(v, dict)}
    for k, v in flat.items():
        lines.append(f'{k} = "{v}"\n')
    for section, vals in data.items():
        if isinstance(vals, dict):
            lines.append(f'\n[{section}]\n')
            for k, v in vals.items():
                lines.append(f'{k} = "{v}"\n')
    _atomic_write(path, "".join(lines))


def _strip_json5_comments(text):
    """Remove // line comments and trailing commas for JSON5 compat."""
    text = re.sub(r'//[^\n]*', '', text)
    text = re.sub(r',\s*([}\]])', r'\1', text)
    return text


# ── Core functions ─────────────────────────────────────────────────────

def init_dirs():
    global APPS
    if not APPS:
        APPS = _build_apps()
    for app in APPS.values():
        app.presets_dir.mkdir(parents=True, exist_ok=True)
        app.backup_dir.mkdir(parents=True, exist_ok=True)
        app.settings_file.parent.mkdir(parents=True, exist_ok=True)
        if app.settings_file2:
            app.settings_file2.parent.mkdir(parents=True, exist_ok=True)
    # Seed examples for claude (backward compat)
    claude = APPS["claude"]
    if not any(claude.presets_dir.glob("*.json")):
        for name, data in claude.examples.items():
            p = claude.presets_dir / f"{name}.json"
            p.write_text(json.dumps(data, indent=2, ensure_ascii=False))
            _chmod600(p)
    # Seed examples for other apps
    for app_name in ("codex", "gemini", "opencode"):
        app = APPS[app_name]
        if not any(app.presets_dir.glob("*.*")):
            for name, data in app.examples.items():
                ext = _preset_ext(app)
                p = app.presets_dir / f"{name}{ext}"
                _write_preset_file(p, data, app)
                _chmod600(p)


def _preset_ext(app):
    if app.fmt == "env":
        return ".env"
    elif app.name == "codex":
        return ".json"  # stores both auth + config sections
    return ".json"


def _write_preset_file(path, data, app):
    """Write preset data in the app's native format."""
    if app.fmt == "env":
        _write_env_file(path, data)
    elif app.name == "codex":
        _atomic_write(path, json.dumps(data, indent=2, ensure_ascii=False))
    else:
        _atomic_write(path, json.dumps(data, indent=2, ensure_ascii=False))


def list_presets():
    """List preset files for the current app."""
    app = _app()
    if app.fmt == "env":
        return sorted(app.presets_dir.glob("*.env"), key=lambda p: p.stem)
    return sorted(app.presets_dir.glob("*.json"), key=lambda p: p.stem)


def detect_active_by_content():
    app = _app()
    if not app.settings_file.exists():
        return None
    try:
        current = _read_settings(app)
    except Exception:
        return None
    for p in list_presets():
        try:
            data, _ = parse_preset(p)
            if data == current:
                return p.stem
        except Exception:
            pass
    return None


def _read_settings(app):
    """Read current live settings for an app."""
    if app.fmt == "env":
        return _read_env_file(app.settings_file)
    elif app.name == "codex":
        auth = json.loads(app.settings_file.read_text()) if app.settings_file.exists() else {}
        config = _read_toml_simple(app.settings_file2) if app.settings_file2 and app.settings_file2.exists() else {}
        return {"auth": auth, "config": config}
    else:
        text = app.settings_file.read_text()
        if app.fmt == "json5":
            text = _strip_json5_comments(text)
        return json.loads(text)


def _prune_backups_lazy(max_keep=MAX_BACKUPS):
    """Only prune when backups exceed max_keep + 5, reducing disk ops."""
    app = _app()
    try:
        backups = list(app.backup_dir.glob("settings_*.json"))
        if len(backups) <= max_keep + 5:
            return
        backups.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        for old in backups[max_keep:]:
            old.unlink()
    except Exception as e:
        print(f"Warning: backup cleanup failed: {e}", file=sys.stderr)


def get_active():
    app = _app()
    try:
        if app.active_file.exists():
            name = app.active_file.read_text().strip()
            if name:
                for p in list_presets():
                    if p.stem == name:
                        return name
    except Exception:
        pass
    return detect_active_by_content()


def list_backups():
    app = _app()
    return sorted(app.backup_dir.glob("settings_*.json"),
                  key=lambda p: p.stat().st_mtime, reverse=True)


def _backup_current():
    app = _app()
    if not app.settings_file.exists():
        return None
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = app.backup_dir / f"settings_{ts}.json"
    try:
        shutil.copy2(app.settings_file, path)
        _chmod600(path)
        return path
    except Exception:
        return None


def restore_backup(backup_path):
    if not backup_path.exists():
        raise FileNotFoundError(backup_path)
    app = _app()
    _backup_current()
    shutil.copy2(backup_path, app.settings_file)
    _chmod600(app.settings_file)
    app.active_file.write_text("(restored)")
    _chmod600(app.active_file)
    _prune_backups_lazy()


def activate(preset_path):
    app = _app()
    _backup_current()
    data, err = parse_preset(preset_path)
    if err:
        raise ValueError(f"Invalid preset: {err}")

    if app.fmt == "env":
        _write_env_file(app.settings_file, data)
    elif app.name == "codex":
        auth = data.get("auth", {})
        config = data.get("config", {})
        _atomic_write(app.settings_file, json.dumps(auth, indent=2, ensure_ascii=False))
        _chmod600(app.settings_file)
        if app.settings_file2:
            _write_toml_simple(app.settings_file2, config)
            _chmod600(app.settings_file2)
    else:
        serialized = json.dumps(data, indent=2, ensure_ascii=False)
        _atomic_write(app.settings_file, serialized)
        _chmod600(app.settings_file)

    app.active_file.write_text(preset_path.stem)
    _chmod600(app.active_file)
    _prune_backups_lazy()


def mask_key(s):
    if not s:
        return "(none)"
    if len(s) <= 12:
        return "***"
    return s[:6] + "***" + s[-4:]


def parse_preset(path):
    app = _app()
    try:
        if app.fmt == "env":
            return _read_env_file(path), None
        elif app.fmt in ("json", "json5"):
            text = path.read_text()
            if app.fmt == "json5":
                text = _strip_json5_comments(text)
            return json.loads(text), None
        else:
            return json.loads(path.read_text()), None
    except Exception as e:
        return None, str(e)


def _curses_import():
    """Lazy import curses — only when entering TUI."""
    import curses
    return curses


def open_editor(path):
    curses = _curses_import()
    editor = os.environ.get("EDITOR", "vi")
    curses.endwin()
    try:
        cmd = shlex.split(editor) + [str(path)]
        subprocess.run(cmd)
    except Exception as e:
        print(f"Error launching editor: {e}", file=sys.stderr)
        input("Press Enter to continue...")
    finally:
        try:
            curses.doupdate()
        except Exception:
            pass


def _generate_diff(preset_path):
    app = _app()
    current_text = ""
    if app.settings_file.exists():
        try:
            current_text = app.settings_file.read_text()
        except Exception:
            pass
    try:
        preset_text = preset_path.read_text()
    except Exception as e:
        return None, f"Error reading preset: {e}"
    diff = list(difflib.unified_diff(
        current_text.splitlines(keepends=True),
        preset_text.splitlines(keepends=True),
        fromfile=str(app.settings_file),
        tofile=str(preset_path),
    ))
    if not diff:
        return "", None
    return "".join(diff), None


def show_diff(preset_path, in_curses=False):
    diff_text, err = _generate_diff(preset_path)
    if err:
        print(err, file=sys.stderr)
        return
    if not diff_text:
        print("No differences.")
        return
    pager = os.environ.get("PAGER", "less")
    if in_curses:
        curses = _curses_import()
        curses.endwin()
    try:
        proc = subprocess.Popen(shlex.split(pager), stdin=subprocess.PIPE)
        proc.stdin.write(diff_text.encode("utf-8"))
        proc.stdin.close()
        proc.wait()
    except Exception:
        print(diff_text)
        if in_curses:
            input("Press Enter to continue...")
    finally:
        if in_curses:
            try:
                curses = _curses_import()
                curses.doupdate()
            except Exception:
                pass


# ── TUI ────────────────────────────────────────────────────────────────

class TUI:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.presets = []
        self.all_presets = []
        self.selected = 0
        self.scroll = 0
        self.message = ""
        self.message_type = "info"
        self.confirm_action = None
        self.input_mode = None
        self.input_buffer = ""
        self.input_prompt = ""
        self.filter_text = ""
        self.in_search = False
        self.cached_active = None
        self._detail_cache = {}  # path -> (mtime, data, err)
        self.refresh()

    def refresh(self):
        self.all_presets = list_presets()
        self._apply_filter()
        self._detail_cache.pop("__stale__", None)
        if self.selected >= len(self.presets):
            self.selected = max(0, len(self.presets) - 1)

    def _apply_filter(self):
        if self.filter_text:
            q = self.filter_text.lower()
            self.presets = [p for p in self.all_presets if q in p.stem.lower()]
        else:
            self.presets = list(self.all_presets)

    def update_active(self):
        self.cached_active = get_active()

    def setup_colors(self):
        curses = _curses_import()
        try:
            curses.start_color()
            curses.use_default_colors()
            curses.init_pair(1, curses.COLOR_CYAN, -1)
            curses.init_pair(2, curses.COLOR_GREEN, -1)
            curses.init_pair(3, curses.COLOR_YELLOW, -1)
            curses.init_pair(4, curses.COLOR_RED, -1)
            curses.init_pair(5, curses.COLOR_MAGENTA, -1)
            curses.init_pair(6, curses.COLOR_WHITE, curses.COLOR_BLUE)
            curses.init_pair(7, curses.COLOR_BLACK, curses.COLOR_CYAN)
            curses.init_pair(8, curses.COLOR_BLACK, curses.COLOR_GREEN)
        except Exception:
            pass

    def set_message(self, msg, mtype="info"):
        self.message = msg
        self.message_type = mtype

    def safe_addstr(self, y, x, text, attr=0):
        curses = _curses_import()
        try:
            self.stdscr.addstr(y, x, text, attr)
        except curses.error:
            pass

    def draw(self):
        curses = _curses_import()
        self.stdscr.erase()
        h, w = self.stdscr.getmaxyx()
        if h < MIN_H or w < MIN_W:
            self.safe_addstr(0, 0, f"Terminal too small (need >= {MIN_W}x{MIN_H})")
            self.stdscr.refresh()
            return

        # Row 0: title
        title = " clap — Multi-Tool Profile Manager "
        self.safe_addstr(0, 0, title.center(w),
                         curses.color_pair(1) | curses.A_BOLD | curses.A_REVERSE)

        # Row 1: App tabs
        x = 2
        for app_name in APP_ORDER:
            label = f" {APPS[app_name].label} "
            if app_name == _cur_app_name:
                self.safe_addstr(1, x, label,
                                 curses.color_pair(2) | curses.A_BOLD | curses.A_REVERSE)
            else:
                self.safe_addstr(1, x, label, curses.A_DIM)
            x += len(label) + 1
        self.safe_addstr(1, x, "  Tab: switch", curses.A_DIM)
        self.safe_addstr(1, x + 10 + len("  Tab: switch"), "  p: presets", curses.A_DIM)
        if _cur_app_name == "claude":
            self.safe_addstr(1, x + 10 + len("  Tab: switch  p: presets"), "  m: MCP", curses.A_DIM)

        # Row 2: Active
        app = _app()
        active = self.cached_active
        active_str = active or "(none)"
        self.safe_addstr(2, 0, f"  Active : ", curses.A_DIM)
        self.safe_addstr(2, 10, active_str[:w - 11],
                         curses.color_pair(2) | curses.A_BOLD)

        # Row 3: Target
        target_str = str(app.settings_file)
        if app.settings_file2:
            target_str += f" + {app.settings_file2}"
        self.safe_addstr(3, 0, f"  Target : {target_str}"[:w - 1], curses.A_DIM)

        fb = 1 if self.filter_text else 0
        if fb:
            self.safe_addstr(4, 0, f"  Filter : {self.filter_text}"[:w - 1],
                             curses.color_pair(3))
        header_row = 5 + fb
        list_h = h - 7 - fb  # -1 for header + tabs offset (we added 1 row)
        list_w = max(MIN_LIST_W, w // 3)
        detail_x = list_w + 2
        detail_w = w - detail_x - 1

        self.safe_addstr(header_row, 0, "Presets".ljust(list_w),
                         curses.A_UNDERLINE | curses.A_BOLD)
        self.safe_addstr(header_row, detail_x, "Details".ljust(detail_w),
                         curses.A_UNDERLINE | curses.A_BOLD)

        if not self.presets:
            self.safe_addstr(header_row + 2, 2, "(no presets, press 'n' to create)",
                             curses.A_DIM)
        else:
            visible = list_h - 1
            if self.selected < self.scroll:
                self.scroll = self.selected
            elif self.selected >= self.scroll + visible:
                self.scroll = self.selected - visible + 1

            for i, p in enumerate(self.presets[self.scroll:self.scroll + visible]):
                idx = self.scroll + i
                row = header_row + 1 + i
                name = p.stem
                marker = "* " if name == active else "  "
                line = f"{marker}{name}"[:list_w - 1].ljust(list_w - 1)
                if idx == self.selected:
                    self.safe_addstr(row, 0, " " + line,
                                     curses.color_pair(6) | curses.A_BOLD)
                elif name == active:
                    self.safe_addstr(row, 0, " " + line,
                                     curses.color_pair(8) | curses.A_BOLD)
                else:
                    self.safe_addstr(row, 0, " " + line)

        if self.presets:
            sel = self.presets[self.selected]
            mtime = sel.stat().st_mtime if sel.exists() else 0
            cached = self._detail_cache.get(sel)
            if not cached or cached[0] != mtime:
                data, err = parse_preset(sel)
                self._detail_cache[sel] = (mtime, data, err)
                # Keep cache bounded
                if len(self._detail_cache) > 20:
                    oldest = next(iter(self._detail_cache))
                    del self._detail_cache[oldest]
            data, err = self._detail_cache[sel][1], self._detail_cache[sel][2]
            self._draw_detail(header_row + 1, detail_x, list_h, detail_w, sel, data, err)

        # Key hints
        keys = [
            ("↑↓/jk", "Move"), ("Enter", "Activate"), ("e", "Edit"),
            ("n", "New"), ("d", "Dup"), ("R", "Rename"),
            ("D", "Delete"), ("/", "Filter"), ("=", "Diff"),
            ("b", "Backups"), ("r", "Reload"), ("o", "Finder"),
            ("Tab", "App"), ("p", "Presets"),
        ]
        if _cur_app_name == "claude":
            keys.append(("m", "MCP"))
        keys.append(("q", "Quit"))

        x = 0
        fy = h - 2
        for k, lbl in keys:
            piece = f" {k} "
            text = f" {lbl}  "
            if x + len(piece) + len(text) >= w:
                fy += 1
                x = 0
                if fy >= h:
                    break
            self.safe_addstr(fy, x, piece, curses.color_pair(7) | curses.A_BOLD)
            x += len(piece)
            self.safe_addstr(fy, x, text, curses.A_DIM)
            x += len(text)

        # Status line
        if self.in_search:
            prompt = f"Filter: {self.filter_text}"
            self.safe_addstr(h - 1, 0, prompt[:w - 1], curses.color_pair(1) | curses.A_BOLD)
            try:
                self.stdscr.move(h - 1, min(w - 1, len(prompt)))
            except curses.error:
                pass
        elif self.input_mode:
            self.safe_addstr(h - 1, 0,
                             (self.input_prompt + self.input_buffer)[:w - 1])
            try:
                self.stdscr.move(h - 1,
                                 min(w - 1,
                                     len(self.input_prompt) + len(self.input_buffer)))
            except curses.error:
                pass
        elif self.confirm_action:
            self.safe_addstr(h - 1, 0, self.confirm_action[0][:w - 1],
                             curses.color_pair(3) | curses.A_BOLD)
        elif self.message:
            color = {
                "info": curses.color_pair(1),
                "success": curses.color_pair(2),
                "warn": curses.color_pair(3),
                "error": curses.color_pair(4),
            }.get(self.message_type, curses.color_pair(1))
            self.safe_addstr(h - 1, 0, self.message[:w - 1], color)

        self.stdscr.refresh()

    def _draw_detail(self, y, x, h, w, path, data, err):
        curses = _curses_import()
        if err:
            self.safe_addstr(y, x, f"Parse error: {err}"[:w],
                             curses.color_pair(4))
            return

        app = _app()
        if app.fmt == "env":
            self._draw_detail_env(y, x, h, w, path, data)
        elif app.name == "codex":
            self._draw_detail_codex(y, x, h, w, path, data)
        else:
            self._draw_detail_json(y, x, h, w, path, data)

    def _draw_detail_json(self, y, x, h, w, path, data):
        curses = _curses_import()
        env = data.get("env", {}) if isinstance(data, dict) else {}
        perms = data.get("permissions", {}) if isinstance(data, dict) else {}

        api_key = env.get("ANTHROPIC_API_KEY") or env.get("ANTHROPIC_AUTH_TOKEN", "")
        base_url = env.get("ANTHROPIC_BASE_URL", "(default)")
        model = env.get("ANTHROPIC_MODEL", "(default)")
        small = env.get("ANTHROPIC_SMALL_FAST_MODEL", "(default)")
        max_tok = env.get("CLAUDE_CODE_MAX_OUTPUT_TOKENS", "(default)")
        auth_kind = "AUTH_TOKEN" if env.get("ANTHROPIC_AUTH_TOKEN") else "API_KEY"

        rows = [
            ("File:", path.name, 0),
            ("", "─" * min(w - 1, 30), curses.A_DIM),
            (f"{auth_kind}:", mask_key(api_key), curses.color_pair(3)),
            ("Base URL:", base_url, 0),
            ("Model:", model, curses.color_pair(1)),
            ("Small Model:", small, 0),
            ("Max Output:", str(max_tok), 0),
            ("", "─" * min(w - 1, 30), curses.A_DIM),
            ("Mode:", perms.get("defaultMode", "default"), curses.color_pair(3)),
            ("Allow:", "", 0),
        ]
        for a in perms.get("allow", []) or ["(none)"]:
            rows.append(("", "  + " + str(a), curses.color_pair(2)))
        rows.append(("Deny:", "", 0))
        for d in perms.get("deny", []) or ["(none)"]:
            rows.append(("", "  - " + str(d), curses.color_pair(4)))

        extras = {k: v for k, v in env.items() if k not in {
            "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN",
            "ANTHROPIC_BASE_URL", "ANTHROPIC_MODEL",
            "ANTHROPIC_SMALL_FAST_MODEL",
            "CLAUDE_CODE_MAX_OUTPUT_TOKENS"
        }}
        if extras:
            rows.append(("", "─" * min(w - 1, 30), curses.A_DIM))
            rows.append(("Extra Env:", "", 0))
            for k, v in extras.items():
                rows.append(("", f"  {k}={v}", 0))

        for i, (label, value, attr) in enumerate(rows):
            if i >= h - 1:
                break
            if label:
                self.safe_addstr(y + i, x, label[:w],
                                 curses.color_pair(5) | curses.A_BOLD)
                self.safe_addstr(y + i, x + LABEL_WIDTH,
                                 str(value)[:max(0, w - LABEL_WIDTH)], attr)
            else:
                self.safe_addstr(y + i, x, str(value)[:w], attr)

    def _draw_detail_env(self, y, x, h, w, path, data):
        curses = _curses_import()
        rows = [
            ("File:", path.name, 0),
            ("", "─" * min(w - 1, 30), curses.A_DIM),
        ]
        sensitive_keys = {"API_KEY", "AUTH_TOKEN", "TOKEN", "SECRET"}
        for k, v in sorted(data.items()):
            is_sensitive = any(s in k.upper() for s in sensitive_keys)
            display = mask_key(v) if is_sensitive else v
            color = curses.color_pair(3) if is_sensitive else 0
            rows.append((f"{k}:", display, color))

        for i, (label, value, attr) in enumerate(rows):
            if i >= h - 1:
                break
            if label:
                self.safe_addstr(y + i, x, label[:w],
                                 curses.color_pair(5) | curses.A_BOLD)
                self.safe_addstr(y + i, x + LABEL_WIDTH,
                                 str(value)[:max(0, w - LABEL_WIDTH)], attr)
            else:
                self.safe_addstr(y + i, x, str(value)[:w], attr)

    def _draw_detail_codex(self, y, x, h, w, path, data):
        curses = _curses_import()
        auth = data.get("auth", {}) if isinstance(data, dict) else {}
        config = data.get("config", {}) if isinstance(data, dict) else {}

        rows = [
            ("File:", path.name, 0),
            ("", "─" * min(w - 1, 30), curses.A_DIM),
            ("[Auth]", "", 0),
            ("API Key:", mask_key(auth.get("OPENAI_API_KEY", "")),
             curses.color_pair(3)),
            ("", "─" * min(w - 1, 30), curses.A_DIM),
            ("[Config]", "", 0),
            ("Model:", str(config.get("model", "(default)")), curses.color_pair(1)),
            ("Provider:", str(config.get("model_provider", "(default)")), 0),
            ("Base URL:", str(config.get("base_url", "(default)")), 0),
        ]
        for i, (label, value, attr) in enumerate(rows):
            if i >= h - 1:
                break
            if label:
                self.safe_addstr(y + i, x, label[:w],
                                 curses.color_pair(5) | curses.A_BOLD)
                self.safe_addstr(y + i, x + LABEL_WIDTH,
                                 str(value)[:max(0, w - LABEL_WIDTH)], attr)
            else:
                self.safe_addstr(y + i, x, str(value)[:w], attr)

    def activate_selected(self):
        if not self.presets:
            return
        p = self.presets[self.selected]
        try:
            activate(p)
            self.set_message(f"Activated: {p.stem}  (previous backed up)",
                             "success")
        except Exception as e:
            self.set_message(f"Activation failed: {e}", "error")

    def edit_selected(self):
        if not self.presets:
            return
        p = self.presets[self.selected]
        open_editor(p)
        self.refresh()
        self.set_message(f"Edited: {p.stem}", "info")

    def new_preset(self):
        self.input_mode = MODE_NEW
        app = _app()
        ext = _preset_ext(app)
        self.input_prompt = f"New preset name (without {ext}): "
        self.input_buffer = ""

    def duplicate_selected(self):
        if not self.presets:
            return
        self.input_mode = MODE_DUP
        self.input_prompt = "Duplicate as: "
        self.input_buffer = self.presets[self.selected].stem + "-copy"

    def rename_selected(self):
        if not self.presets:
            return
        self.input_mode = MODE_RENAME
        self.input_prompt = "Rename to: "
        self.input_buffer = self.presets[self.selected].stem

    def delete_selected(self):
        if not self.presets:
            return
        p = self.presets[self.selected]
        self.confirm_action = (
            f"Delete preset '{p.stem}'? press y to confirm, any other to cancel ",
            lambda: self._do_delete(p)
        )

    def _do_delete(self, p):
        try:
            p.unlink()
            self.refresh()
            self.set_message(f"Deleted: {p.stem}", "warn")
        except Exception as e:
            self.set_message(f"Delete failed: {e}", "error")

    def _select_by_path(self, target):
        for i, p in enumerate(self.presets):
            if p == target:
                self.selected = i
                return

    def open_dir(self):
        app = _app()
        try:
            if sys.platform == "darwin":
                subprocess.run(["open", str(app.presets_dir)])
            else:
                subprocess.run(["xdg-open", str(app.presets_dir)])
            self.set_message(f"Opened {app.presets_dir}", "info")
        except Exception as e:
            self.set_message(f"Open dir failed: {e}", "error")

    def switch_app(self, app_name):
        global _cur_app_name
        _cur_app_name = app_name
        self._detail_cache.clear()
        self.refresh()
        self.update_active()
        self.set_message(f"Switched to {APPS[app_name].label}", "info")

    def handle_input(self, key):
        curses = _curses_import()
        app = _app()
        if key in (10, 13):
            name = self.input_buffer.strip()
            if name:
                ext = _preset_ext(app)
                target = app.presets_dir / f"{name}{ext}"
                if target.exists():
                    self.set_message(f"'{name}' already exists", "error")
                    return
                if self.input_mode == MODE_NEW:
                    _write_preset_file(target, app.default_template, app)
                    _chmod600(target)
                    self.refresh()
                    self._select_by_path(target)
                    open_editor(target)
                    self.set_message(f"Created: {name}", "success")
                elif self.input_mode == MODE_DUP:
                    src = self.presets[self.selected]
                    shutil.copy2(src, target)
                    _chmod600(target)
                    self.refresh()
                    self._select_by_path(target)
                    self.set_message(f"Duplicated to: {name}", "success")
                elif self.input_mode == MODE_RENAME:
                    src = self.presets[self.selected]
                    src.rename(target)
                    _chmod600(target)
                    self.refresh()
                    self._select_by_path(target)
                    self.set_message(f"Renamed to: {name}", "success")
            self.input_mode = None
            self.input_buffer = ""
        elif key == 27:
            self.input_mode = None
            self.input_buffer = ""
            self.set_message("Cancelled", "info")
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            self.input_buffer = self.input_buffer[:-1]
        elif 32 <= key < 127:
            self.input_buffer += chr(key)

    def handle_confirm(self, key):
        _, action = self.confirm_action
        if key in (ord('y'), ord('Y')):
            action()
        else:
            self.set_message("Cancelled", "info")
        self.confirm_action = None

    def diff_selected(self):
        if not self.presets:
            return
        show_diff(self.presets[self.selected], in_curses=True)
        self.set_message("Diff viewed", "info")

    def enter_search(self):
        self.in_search = True
        self.filter_text = ""
        self._apply_filter()
        self.selected = 0
        self.scroll = 0

    def exit_search(self):
        self.in_search = False

    def handle_search(self, key):
        curses = _curses_import()
        if key == 27:
            self.filter_text = ""
            self._apply_filter()
            self.exit_search()
            self.selected = 0
            self.set_message("Filter cleared", "info")
        elif key in (10, 13):
            self.exit_search()
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            self.filter_text = self.filter_text[:-1]
            self._apply_filter()
            if self.selected >= len(self.presets):
                self.selected = max(0, len(self.presets) - 1)
        elif 32 <= key < 127:
            self.filter_text += chr(key)
            self._apply_filter()
            self.selected = 0

    def open_backups(self):
        curses = _curses_import()
        backups = list_backups()
        if not backups:
            self.set_message("No backups available", "warn")
            return
        sel = 0
        scroll = 0
        while True:
            self.stdscr.erase()
            h, w = self.stdscr.getmaxyx()
            self.safe_addstr(0, 0, " Backups (Enter=restore, Esc=back) ".center(w),
                             curses.color_pair(1) | curses.A_BOLD | curses.A_REVERSE)
            visible = h - 4
            if sel < scroll:
                scroll = sel
            elif sel >= scroll + visible:
                scroll = sel - visible + 1
            for i, b in enumerate(backups[scroll:scroll + visible]):
                idx = scroll + i
                line = b.name[:w - 2]
                if idx == sel:
                    self.safe_addstr(2 + i, 0, (" " + line).ljust(w - 1),
                                     curses.color_pair(6) | curses.A_BOLD)
                else:
                    self.safe_addstr(2 + i, 0, "  " + line)
            self.safe_addstr(h - 1, 0,
                             f" {len(backups)} backups — ↑↓/jk move  Enter restore  Esc back "[:w - 1],
                             curses.A_DIM)
            self.stdscr.refresh()
            key = self.stdscr.getch()
            if key in (ord('q'), 27):
                break
            elif key in (curses.KEY_UP, ord('k')) and sel > 0:
                sel -= 1
            elif key in (curses.KEY_DOWN, ord('j')) and sel < len(backups) - 1:
                sel += 1
            elif key in (10, 13):
                b = backups[sel]
                self.confirm_action = (
                    f"Restore '{b.name}'? press y to confirm, any other to cancel ",
                    lambda bp=b: self._do_restore(bp)
                )
                break
        self.refresh()
        self.update_active()

    def _do_restore(self, backup_path):
        try:
            restore_backup(backup_path)
            self.set_message(f"Restored: {backup_path.name}", "success")
        except Exception as e:
            self.set_message(f"Restore failed: {e}", "error")

    # ── Provider Preset Picker ──────────────────────────────────────

    def open_provider_picker(self):
        curses = _curses_import()
        providers = BUILTIN_PROVIDERS.get(_cur_app_name, {})
        if not providers:
            self.set_message("No built-in providers for this app", "warn")
            return
        categories = list(providers.keys())
        cat_sel = 0
        item_sel = 0
        while True:
            self.stdscr.erase()
            h, w = self.stdscr.getmaxyx()
            self.safe_addstr(0, 0, " Built-in Providers (Enter=import, Esc=back) ".center(w),
                             curses.color_pair(1) | curses.A_BOLD | curses.A_REVERSE)
            cat_w = min(22, w // 4)
            # Left column: categories
            for i, cat in enumerate(categories):
                attr = curses.color_pair(6) | curses.A_BOLD if i == cat_sel else 0
                self.safe_addstr(2 + i, 1, cat[:cat_w - 1].ljust(cat_w - 1), attr)
            # Right column: current category's providers
            items = providers[categories[cat_sel]]
            for i, item in enumerate(items):
                line = f"  {item['name']}"
                attr = curses.color_pair(6) | curses.A_BOLD if i == item_sel else 0
                self.safe_addstr(2 + i, cat_w + 2, line[:w - cat_w - 4], attr)
            self.safe_addstr(h - 1, 0,
                             " ←→: category  ↑↓: provider  Enter: import  Esc: back "[:w - 1],
                             curses.A_DIM)
            self.stdscr.refresh()
            key = self.stdscr.getch()
            if key == 27:
                break
            elif key in (curses.KEY_LEFT, ord('h')) and cat_sel > 0:
                cat_sel -= 1
                item_sel = 0
            elif key in (curses.KEY_RIGHT, ord('l')) and cat_sel < len(categories) - 1:
                cat_sel += 1
                item_sel = 0
            elif key in (curses.KEY_UP, ord('k')) and item_sel > 0:
                item_sel -= 1
            elif key in (curses.KEY_DOWN, ord('j')) and item_sel < len(items) - 1:
                item_sel += 1
            elif key in (10, 13):
                self._import_builtin_provider(items[item_sel])
                break

    def _import_builtin_provider(self, provider):
        """Write built-in provider as a new preset, then open editor."""
        app = _app()
        name = provider["name"]
        ext = _preset_ext(app)
        target = app.presets_dir / f"{name}{ext}"
        if app.fmt == "env":
            data = {k: v for k, v in provider.items() if k != "name"}
        elif app.name == "codex":
            data = {"auth": provider.get("auth", {}),
                    "config": provider.get("config", {})}
        elif "providers" in provider:
            data = {"providers": provider.get("providers", {})}
        else:
            env = {k: v for k, v in provider.items()
                   if k not in ("name", "permissions")
                   and not isinstance(v, (list, dict))}
            perms = provider.get("permissions",
                                  {"defaultMode": "default", "allow": [], "deny": []})
            data = {"env": env, "permissions": perms}
        _write_preset_file(target, data, app)
        _chmod600(target)
        self.refresh()
        self._select_by_path(target)
        open_editor(target)
        self.set_message(f"Imported '{name}' — fill in your API key", "success")

    # ── MCP Manager ──────────────────────────────────────────────────

    def open_mcp_manager(self):
        curses = _curses_import()
        if _cur_app_name != "claude":
            self.set_message("MCP management is only available for Claude Code", "warn")
            return
        app = _app()
        try:
            settings = json.loads(app.settings_file.read_text()) if app.settings_file.exists() else {}
        except Exception as e:
            self.set_message(f"Cannot read settings: {e}", "error")
            return
        mcp_servers = settings.get("mcpServers", {}) if isinstance(settings, dict) else {}
        names = list(mcp_servers.keys())
        sel = 0
        while True:
            self.stdscr.erase()
            h, w = self.stdscr.getmaxyx()
            self.safe_addstr(0, 0, " MCP Servers (a=add, D=delete, Esc=back) ".center(w),
                             curses.color_pair(1) | curses.A_BOLD | curses.A_REVERSE)
            if not names:
                self.safe_addstr(2, 2, "(no MCP servers configured)", curses.A_DIM)
            else:
                visible = max(0, h - 4)
                for i, name in enumerate(names):
                    if i >= visible:
                        break
                    cfg = mcp_servers[name]
                    cmd_str = cfg.get("command", "") + " " + " ".join(cfg.get("args", []))
                    line = f"{name}  [{cmd_str.strip()}]"
                    attr = curses.color_pair(6) | curses.A_BOLD if i == sel else 0
                    self.safe_addstr(2 + i, 2, line[:w - 4], attr)
            self.safe_addstr(h - 1, 0,
                             " ↑↓: select  a: add  D: delete  Esc: back "[:w - 1],
                             curses.A_DIM)
            self.stdscr.refresh()
            key = self.stdscr.getch()
            if key == 27:
                break
            elif key in (curses.KEY_UP, ord('k')) and sel > 0:
                sel -= 1
            elif key in (curses.KEY_DOWN, ord('j')) and sel < len(names) - 1:
                sel += 1
            elif key == ord('a'):
                new_cfg = self._prompt_new_mcp()
                if new_cfg:
                    mcp_servers[new_cfg["name"]] = {
                        "command": new_cfg["command"],
                        "args": new_cfg["args"],
                        "type": new_cfg.get("type", "stdio"),
                    }
                    names = list(mcp_servers.keys())
                    settings["mcpServers"] = mcp_servers
                    _atomic_write(app.settings_file,
                                  json.dumps(settings, indent=2, ensure_ascii=False))
                    _chmod600(app.settings_file)
                    self.set_message(f"Added MCP server: {new_cfg['name']}", "success")
            elif key == ord('D') and names:
                deleted = names[sel]
                del mcp_servers[deleted]
                names = list(mcp_servers.keys())
                sel = min(sel, max(0, len(names) - 1))
                settings["mcpServers"] = mcp_servers
                _atomic_write(app.settings_file,
                              json.dumps(settings, indent=2, ensure_ascii=False))
                _chmod600(app.settings_file)
                self.set_message(f"Deleted MCP server: {deleted}", "warn")

    def _readline(self, prompt):
        """Read a single line of input at the status bar. Returns None on Esc."""
        curses = _curses_import()
        buf = ""
        h, w = self.stdscr.getmaxyx()
        try:
            curses.curs_set(1)
        except Exception:
            pass
        while True:
            self.safe_addstr(h - 1, 0,
                             (prompt + buf)[:w - 1] + " " * max(0, w - len(prompt) - len(buf) - 1))
            try:
                self.stdscr.move(h - 1, min(w - 1, len(prompt) + len(buf)))
            except curses.error:
                pass
            self.stdscr.refresh()
            key = self.stdscr.getch()
            if key == 27:
                try:
                    curses.curs_set(0)
                except Exception:
                    pass
                return None
            elif key in (10, 13):
                break
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                buf = buf[:-1]
            elif 32 <= key < 127:
                buf += chr(key)
        try:
            curses.curs_set(0)
        except Exception:
            pass
        return buf.strip()

    def _prompt_new_mcp(self):
        """Prompt for MCP server fields: name, command, args."""
        fields = [
            ("MCP server name (e.g. fetch): ", "name"),
            ("Command (e.g. uvx): ", "command"),
            ("Args (space-separated, e.g. mcp-server-fetch): ", "args_str"),
        ]
        result = {}
        for prompt, key in fields:
            val = self._readline(prompt)
            if val is None:
                return None
            result[key] = val
        result["args"] = result.pop("args_str").split()
        return result

    # ── Main loop ────────────────────────────────────────────────────

    def loop(self):
        curses = _curses_import()
        try:
            curses.curs_set(0)
        except Exception:
            pass
        self.setup_colors()
        self.update_active()

        while True:
            self.draw()
            try:
                key = self.stdscr.getch()
            except KeyboardInterrupt:
                break

            if self.in_search:
                try:
                    curses.curs_set(1)
                except Exception:
                    pass
                self.handle_search(key)
                try:
                    curses.curs_set(0)
                except Exception:
                    pass
                continue

            if self.input_mode:
                try:
                    curses.curs_set(1)
                except Exception:
                    pass
                self.handle_input(key)
                try:
                    curses.curs_set(0)
                except Exception:
                    pass
                continue

            if self.confirm_action:
                self.handle_confirm(key)
                continue

            self.message = ""

            if key in (ord('q'), ord('Q')):
                break
            elif key in (curses.KEY_UP, ord('k')):
                if self.selected > 0:
                    self.selected -= 1
            elif key in (curses.KEY_DOWN, ord('j')):
                if self.selected < len(self.presets) - 1:
                    self.selected += 1
            elif key in (10, 13):
                self.activate_selected()
                self.update_active()
            elif key == ord('e'):
                self.edit_selected()
            elif key == ord('n'):
                self.new_preset()
            elif key == ord('d'):
                self.duplicate_selected()
            elif key == ord('R'):
                self.rename_selected()
            elif key == ord('D'):
                self.delete_selected()
            elif key == ord('/'):
                self.enter_search()
            elif key == ord('='):
                self.diff_selected()
            elif key == ord('b'):
                self.open_backups()
            elif key == ord('r'):
                self.refresh()
                self.update_active()
                self.set_message("Reloaded", "info")
            elif key == ord('o'):
                self.open_dir()
            elif key == ord('\t'):
                idx = APP_ORDER.index(_cur_app_name)
                self.switch_app(APP_ORDER[(idx + 1) % len(APP_ORDER)])
            elif key == ord('p'):
                self.open_provider_picker()
            elif key == ord('m'):
                self.open_mcp_manager()
            elif key == curses.KEY_RESIZE:
                pass


# ── Update ─────────────────────────────────────────────────────────────

def _cmd_update():
    import urllib.request
    REPO = "pterchan/clap"
    BRANCH = "main"
    url = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/clap.py"
    print(f"Fetching latest clap from {url} ...")
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            new_src = resp.read().decode("utf-8")
    except Exception as e:
        print(f"Update failed: {e}", file=sys.stderr)
        sys.exit(1)

    remote_version = None
    for line in new_src.splitlines():
        if line.startswith("VERSION"):
            try:
                remote_version = line.split("=")[1].strip().strip('"').strip("'")
            except Exception:
                pass
            break

    if remote_version and remote_version == VERSION:
        print(f"Already up to date (v{VERSION}).")
        return

    self_path = Path(sys.argv[0]).resolve()
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tmp:
        tmp.write(new_src)
        tmp_path = Path(tmp.name)
    try:
        shutil.copy2(tmp_path, self_path)
        os.chmod(self_path, 0o755)
    finally:
        tmp_path.unlink(missing_ok=True)

    if remote_version:
        print(f"Updated v{VERSION} → v{remote_version}")
    else:
        print("Updated successfully.")


# ── CLI main ───────────────────────────────────────────────────────────

def cli_main():
    global _cur_app_name
    _load_default_app()
    init_dirs()
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        app = _app()

        if cmd in ("ls", "list"):
            active = get_active()
            for p in list_presets():
                marker = " * " if p.stem == active else "   "
                print(f"{marker}{p.stem}")
            return
        if cmd == "use" and len(sys.argv) >= 3:
            ext = _preset_ext(app)
            target = app.presets_dir / f"{sys.argv[2]}{ext}"
            # Also try .json for backward compat
            if not target.exists() and ext != ".json":
                target = app.presets_dir / f"{sys.argv[2]}.json"
            if not target.exists():
                print(f"Preset not found: {sys.argv[2]}")
                sys.exit(1)
            activate(target)
            print(f"Activated: {sys.argv[2]}")
            return
        if cmd == "current":
            print(get_active() or "(unknown)")
            return
        if cmd == "diff" and len(sys.argv) >= 3:
            ext = _preset_ext(app)
            target = app.presets_dir / f"{sys.argv[2]}{ext}"
            if not target.exists() and ext != ".json":
                target = app.presets_dir / f"{sys.argv[2]}.json"
            if not target.exists():
                print(f"Preset not found: {sys.argv[2]}")
                sys.exit(1)
            show_diff(target)
            return
        if cmd == "backups":
            backups = list_backups()
            if not backups:
                print("No backups found.")
            else:
                for b in backups:
                    print(b.name)
            return
        if cmd == "restore" and len(sys.argv) >= 3:
            name = sys.argv[2]
            if name.startswith("settings_"):
                target = app.backup_dir / name
            else:
                target = app.backup_dir / f"settings_{name}.json"
            if not target.exists():
                print(f"Backup not found: {name}")
                sys.exit(1)
            restore_backup(target)
            print(f"Restored: {target.name}")
            return
        if cmd in ("-V", "--version", "version"):
            print(f"clap v{VERSION}")
            return
        if cmd in ("-h", "--help", "help"):
            print("Usage:")
            print("  clap                     open TUI")
            print("  clap ls                  list all presets")
            print("  clap use <name>          activate by name")
            print("  clap current             print active preset name")
            print("  clap diff <name>         diff preset against current settings")
            print("  clap backups             list available backups")
            print("  clap restore <name>      restore a backup (name or timestamp)")
            print("  clap apps                list supported apps")
            print("  clap app <name>          switch default app for CLI commands")
            print("  clap update              update clap to the latest version")
            print(f"\nSupported apps: {', '.join(APP_ORDER)}")
            print(f"Current app: {_cur_app_name}")
            print(f"Presets dir: {app.presets_dir}")
            print(f"Backups dir: {app.backup_dir}")
            return
        if cmd == "apps":
            for a_name in APP_ORDER:
                a = APPS[a_name]
                marker = " * " if a_name == _cur_app_name else "   "
                print(f"{marker}{a_name}  ({a.label}) — {a.settings_file}")
            return
        if cmd == "app" and len(sys.argv) >= 3:
            target = sys.argv[2]
            if target not in APPS:
                print(f"Unknown app: {target}. Available: {', '.join(APP_ORDER)}")
                sys.exit(1)
            _cur_app_name = target
            try:
                DEFAULT_APP_FILE.write_text(target)
                _chmod600(DEFAULT_APP_FILE)
            except Exception:
                pass
            print(f"Switched to {APPS[target].label} ({target})")
            return
        if cmd == "update":
            _cmd_update()
            return

    # Launch TUI
    import curses
    curses.wrapper(lambda s: TUI(s).loop())


if __name__ == "__main__":
    cli_main()
