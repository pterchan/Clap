#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 pterchan
"""
clap v2 — Multi-Tool Profile Manager (TUI)
Manage settings.json profiles for Claude Code, Codex, Gemini CLI, and OpenCode.
"""
import atexit
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

VERSION = "0.2.7"

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
MODE_BACKUP = "backup"

LANG_FILE = CLAP_DIR / "lang"
_cur_lang = "en"


def _restore_mouse_cursor():
    """Restore mouse cursor to default shape."""
    try:
        sys.stdout.write("\033]22;\033\\")
        sys.stdout.flush()
    except Exception:
        pass


atexit.register(_restore_mouse_cursor)


def _load_lang():
    """Detect language from config file, env var, or system locale. Sets _cur_lang."""
    global _cur_lang
    # 1. Config file
    if LANG_FILE.exists():
        try:
            raw = LANG_FILE.read_text().strip()
            if raw in ("zh-CN", "zh-TW", "ja", "en"):
                _cur_lang = raw
                return
        except Exception:
            pass
    # 2. Env var
    env_lang = os.environ.get("CLAP_LANG", "")
    if env_lang:
        raw = env_lang.strip()
        if raw in ("zh-CN", "zh-TW", "ja", "en"):
            _cur_lang = raw
            return
    # 3. System locale (check LANG/LC_ALL env vars)
    loc = os.environ.get("LANG", "") or os.environ.get("LC_ALL", "")
    # Normalize locale codes
    loc_lower = loc.lower().replace("_", "-")
    if any(x in loc_lower for x in ("zh-cn", "zh-hans", "zh_cn")):
        _cur_lang = "zh-CN"
    elif any(x in loc_lower for x in ("zh-tw", "zh-hant", "zh_tw")):
        _cur_lang = "zh-TW"
    elif any(x in loc_lower for x in ("ja", "ja_jp", "ja-jp")):
        _cur_lang = "ja"
    else:
        _cur_lang = "en"


def _t(key, **kwargs):
    """Translate by key for the current language. Falls back to English."""
    if _cur_lang == "en":
        translated = L10N.get("en", {}).get(key, key)
    else:
        translated = L10N.get(_cur_lang, {}).get(key)
        if translated is None:
            translated = L10N.get("en", {}).get(key, key)
    if kwargs:
        return translated.format(**kwargs)
    return translated


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
        print(_t("msg.warning_chmod", path=str(path), error=str(e)), file=sys.stderr)


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
    text = re.sub(r'(?<![:/])//[^\n]*', '', text)
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
            _atomic_write(p, json.dumps(data, indent=2, ensure_ascii=False))
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


def _preset_path_for_name(app, name):
    """Resolve a preset name under the app's presets dir."""
    ext = _preset_ext(app)
    target = app.presets_dir / f"{name}{ext}"
    try:
        ok = str(target.resolve()).startswith(str(app.presets_dir.resolve()))
    except Exception:
        ok = False
    if not name or os.sep in name or (os.altsep and os.altsep in name) or not ok:
        raise ValueError(_t("msg.invalid_name"))
    return target


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


def _has_live_settings(app):
    if app.name == "codex":
        return app.settings_file.exists() or (app.settings_file2 and app.settings_file2.exists())
    return app.settings_file.exists()


def backup_live_as_preset(name):
    """Save the current live settings as a named preset for the active app."""
    app = _app()
    target = _preset_path_for_name(app, name)
    if target.exists():
        raise FileExistsError(_t("msg.already_exists", name=name))
    if not _has_live_settings(app):
        raise FileNotFoundError(_t("msg.no_live_config"))
    data = _read_settings(app)
    _write_preset_file(target, data, app)
    _chmod600(target)
    _atomic_write(app.active_file, target.stem)
    return target


def _prune_backups_lazy(max_keep=MAX_BACKUPS):
    """Only prune when backups exceed max_keep + 5, reducing disk ops."""
    app = _app()
    try:
        backups = list(app.backup_dir.glob("settings_*.json"))
        if len(backups) <= max_keep + 5:
            return
        backups.sort(key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)
        for old in backups[max_keep:]:
            old.unlink()
    except Exception as e:
        print(_t("msg.warning_backup_cleanup", error=str(e)), file=sys.stderr)


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
                  key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)


def _backup_current():
    app = _app()
    if not app.settings_file.exists():
        return None
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = app.backup_dir / f"settings_{ts}.json"
    try:
        _atomic_write(path, app.settings_file.read_text())
        return path
    except Exception:
        return None


def restore_backup(backup_path):
    if not backup_path.exists():
        raise FileNotFoundError(backup_path)
    app = _app()
    _backup_current()
    _atomic_write(app.settings_file, backup_path.read_text())
    _atomic_write(app.active_file, "(restored)")
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

    _atomic_write(app.active_file, preset_path.stem)
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


def _is_placeholder(v):
    """Check if a value is a placeholder/default (not a real credential)."""
    if not v or not isinstance(v, str):
        return True
    v = v.strip()
    if not v:
        return True
    if "..." in v:
        return True
    if "xxxxx" in v:
        return True
    if v.startswith("your-"):
        return True
    return False


def _extract_creds(data, app):
    """Extract api_keys, base_urls, and models from parsed preset data."""
    api_keys = set()
    base_urls = set()
    models = set()

    if app.fmt == "env":
        v = data.get("GEMINI_API_KEY", "") if isinstance(data, dict) else ""
        if not _is_placeholder(v):
            api_keys.add(v)
        v = data.get("GOOGLE_GEMINI_BASE_URL", "") if isinstance(data, dict) else ""
        if not _is_placeholder(v):
            base_urls.add(v)
        v = data.get("GEMINI_MODEL", "") if isinstance(data, dict) else ""
        if not _is_placeholder(v):
            models.add(v)
    elif app.name == "codex":
        auth = data.get("auth", {}) if isinstance(data, dict) else {}
        config = data.get("config", {}) if isinstance(data, dict) else {}
        v = auth.get("OPENAI_API_KEY", "")
        if not _is_placeholder(v):
            api_keys.add(v)
        v = config.get("base_url", "")
        if not _is_placeholder(v):
            base_urls.add(v)
        v = config.get("model", "")
        if not _is_placeholder(v):
            models.add(v)
    elif app.name == "opencode":
        providers = data.get("providers", {}) if isinstance(data, dict) else {}
        for pdata in providers.values():
            if isinstance(pdata, dict):
                v = pdata.get("api_key", "")
                if not _is_placeholder(v):
                    api_keys.add(v)
                v = pdata.get("base_url", "")
                if not _is_placeholder(v):
                    base_urls.add(v)
                v = pdata.get("model", "")
                if not _is_placeholder(v):
                    models.add(v)
    else:
        # claude (fmt="json")
        env = data.get("env", {}) if isinstance(data, dict) else {}
        v = env.get("ANTHROPIC_API_KEY") or env.get("ANTHROPIC_AUTH_TOKEN", "")
        if not _is_placeholder(v):
            api_keys.add(v)
        v = env.get("ANTHROPIC_BASE_URL", "")
        if not _is_placeholder(v):
            base_urls.add(v)
        v = env.get("ANTHROPIC_MODEL", "")
        if not _is_placeholder(v):
            models.add(v)

    return {"api_keys": api_keys, "base_urls": base_urls, "models": models}


def _analyze_preset_overlap(target_path):
    """Compare target preset against stored presets for credential overlap.

    Returns (warn_type, matching_name) where warn_type is:
      'partial' — some fields match but not all (same provider, diff account)
      'none'    — no base_url/api_key match with any stored preset
      None      — no warning needed
    """
    app = _app()
    target_data, err = parse_preset(target_path)
    if err or target_data is None:
        return None, None

    target_creds = _extract_creds(target_data, app)

    # If live config credentials are already covered by any stored preset, no backup needed
    try:
        live_data = _read_settings(app)
        live_creds = _extract_creds(live_data, app)
        for p in list_presets():
            pd, e = parse_preset(p)
            if e or pd is None:
                continue
            pc = _extract_creds(pd, app)
            key_ok = not live_creds["api_keys"] or bool(live_creds["api_keys"] & pc["api_keys"])
            url_ok = not live_creds["base_urls"] or bool(live_creds["base_urls"] & pc["base_urls"])
            if key_ok and url_ok:
                return None, None
    except Exception:
        pass

    other_presets = [p for p in list_presets()
                     if p.resolve() != target_path.resolve()]

    if not other_presets:
        return None, None

    found_any_url_or_key = False

    for p in other_presets:
        other_data, err = parse_preset(p)
        if err or other_data is None:
            continue
        other_creds = _extract_creds(other_data, app)

        key_match = bool(target_creds["api_keys"] & other_creds["api_keys"])
        url_match = bool(target_creds["base_urls"] & other_creds["base_urls"])
        model_match = bool(target_creds["models"] & other_creds["models"])

        if key_match or url_match:
            found_any_url_or_key = True

        any_match = key_match or url_match or model_match

        # all_match: every field present in BOTH must match
        all_match = True
        if target_creds["api_keys"] and other_creds["api_keys"] and not key_match:
            all_match = False
        if target_creds["base_urls"] and other_creds["base_urls"] and not url_match:
            all_match = False
        if target_creds["models"] and other_creds["models"] and not model_match:
            all_match = False

        if any_match and not all_match:
            return "partial", p.stem

    if not found_any_url_or_key:
        return "none", None

    return None, None


def _curses_import():
    """Lazy import curses — only when entering TUI."""
    import curses
    return curses


def open_editor(path):
    curses = _curses_import()
    editor = os.environ.get("EDITOR", "vi")
    curses.endwin()
    try:
        try:
            cmd = shlex.split(editor)
        except ValueError:
            cmd = ["vi"]
        cmd = cmd + [str(path)]
        subprocess.run(cmd)
    except Exception as e:
        print(_t("msg.error_launching_editor", error=str(e)), file=sys.stderr)
        input(_t("msg.press_enter"))
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
        return None, _t("msg.error_reading_preset", error=str(e))
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
        print(_t("msg.no_differences"))
        return
    pager = os.environ.get("PAGER", "less")
    if in_curses:
        curses = _curses_import()
        curses.endwin()
    try:
        try:
            pager_cmd = shlex.split(pager)
        except ValueError:
            pager_cmd = ["less"]
        proc = subprocess.Popen(pager_cmd, stdin=subprocess.PIPE)
        proc.stdin.write(diff_text.encode("utf-8"))
        proc.stdin.close()
        proc.wait()
    except Exception:
        print(diff_text)
        if in_curses:
            input(_t("msg.press_enter"))
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
        self._tab_hitboxes = []   # (row, x_start, x_end, app_name)
        self._key_hitboxes = []   # (row, x_start, x_end, key)
        self._mouse_quit = False
        curses = _curses_import()
        curses.mousemask(curses.ALL_MOUSE_EVENTS)
        # Request arrow mouse cursor (ignored by terminals that don't support it)
        try:
            sys.stdout.write("\033]22;arrow\033\\")
            sys.stdout.flush()
        except Exception:
            pass
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
            self.safe_addstr(0, 0, _t("label.too_small", w=MIN_W, h=MIN_H))
            self.stdscr.refresh()
            return

        # Row 0: title
        title = " " + _t("label.title") + " "
        self.safe_addstr(0, 0, title.center(w),
                         curses.color_pair(1) | curses.A_BOLD | curses.A_REVERSE)

        # Row 1: App tabs
        self._tab_hitboxes = []
        x = 2
        for app_name in APP_ORDER:
            label = f" {APPS[app_name].label} "
            self._tab_hitboxes.append((1, x, x + len(label), app_name))
            if app_name == _cur_app_name:
                self.safe_addstr(1, x, label,
                                 curses.color_pair(2) | curses.A_BOLD | curses.A_REVERSE)
            else:
                self.safe_addstr(1, x, label, curses.A_DIM)
            x += len(label) + 1
        x += 1  # leave breathing room after last tab

        # Row 2: Active + Target (merged)
        app = _app()
        active = self.cached_active
        active_str = active or _t("label.none")
        active_label = "  " + _t("label.active") + " : "
        target_str = str(app.settings_file)
        if app.settings_file2:
            target_str += f" + {app.settings_file2}"
        target_label = _t("label.target") + " : "
        combined = active_label + active_str + "    " + target_label + target_str
        self.safe_addstr(2, 0, combined[:w - 1], curses.A_DIM)

        # Highlight active name in green
        self.safe_addstr(2, len(active_label), active_str,
                         curses.color_pair(2) | curses.A_BOLD)

        fb = 1 if self.filter_text else 0
        if fb:
            filter_label = "  " + _t("label.filter") + " : "
            self.safe_addstr(3, 0, (filter_label + self.filter_text)[:w - 1],
                             curses.color_pair(3))
        header_row = 4 + fb
        list_h = h - 6 - fb
        list_w = max(MIN_LIST_W, w // 3)
        detail_x = list_w + 2
        detail_w = w - detail_x - 1

        self.safe_addstr(header_row, 0, _t("label.presets_hdr").ljust(list_w),
                         curses.A_UNDERLINE | curses.A_BOLD)
        self.safe_addstr(header_row, detail_x, _t("label.details_hdr").ljust(detail_w),
                         curses.A_UNDERLINE | curses.A_BOLD)

        if not self.presets:
            self.safe_addstr(header_row + 2, 2, _t("label.no_presets"),
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

        # Vertical divider between presets and details
        div_x = list_w + 1
        for i in range(list_h):
            self.safe_addstr(header_row + 1 + i, div_x, "│", curses.A_DIM)

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

        # Key hints — grouped with separators
        keys = [
            ("↑↓/jk", _t("hint.move")), ("Enter", _t("hint.activate")),
            ("e", _t("hint.edit")), ("n", _t("hint.new")), ("D", _t("hint.delete")),
            ("|", ""),
            ("/", _t("hint.filter")), ("=", _t("hint.diff")), ("b", _t("hint.backups")),
            ("B", _t("hint.backup_live")),
            ("|", ""),
            ("Tab", _t("hint.app")), ("p", _t("hint.presets")),
        ]
        if _cur_app_name == "claude":
            keys.append(("m", _t("hint.mcp")))
        keys += [
            ("|", ""),
            ("r", _t("hint.reload")), ("o", _t("hint.finder")),
            ("?", _t("hint.help")), ("q", _t("hint.quit")),
        ]

        self._key_hitboxes = []
        x = 0
        fy = h - 2
        for k, lbl in keys:
            if k == "|":
                # Group separator
                sep = " │ "
                if x > 0 and x + len(sep) <= w:
                    self.safe_addstr(fy, x, sep, curses.A_DIM)
                    x += len(sep)
                continue
            piece = f" {k} "
            text = f" {lbl}  "
            if x + len(piece) + len(text) >= w:
                fy += 1
                x = 0
                if fy >= h:
                    break
            self._key_hitboxes.append((fy, x, x + len(piece) + len(text), k))
            self.safe_addstr(fy, x, piece, curses.color_pair(7) | curses.A_BOLD)
            x += len(piece)
            self.safe_addstr(fy, x, text, curses.A_DIM)
            x += len(text)

        # Status line
        if self.in_search:
            prompt = _t("label.filter") + ": " + self.filter_text
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
        base_url = env.get("ANTHROPIC_BASE_URL", _t("label.default"))
        model = env.get("ANTHROPIC_MODEL", _t("label.default"))
        small = env.get("ANTHROPIC_SMALL_FAST_MODEL", _t("label.default"))
        max_tok = env.get("CLAUDE_CODE_MAX_OUTPUT_TOKENS", _t("label.default"))
        auth_kind = _t("detail.auth_token") if env.get("ANTHROPIC_AUTH_TOKEN") else _t("detail.api_key")

        rows = [
            (_t("detail.file") + ":", path.name, 0),
            ("", "─" * min(w - 1, 30), curses.A_DIM),
            (f"{auth_kind}:", mask_key(api_key), curses.color_pair(3)),
            (_t("detail.base_url") + ":", base_url, 0),
            (_t("detail.model") + ":", model, curses.color_pair(1)),
            (_t("detail.small_model") + ":", small, 0),
            (_t("detail.max_output") + ":", str(max_tok), 0),
            ("", "─" * min(w - 1, 30), curses.A_DIM),
            (_t("detail.mode") + ":", perms.get("defaultMode", "default"), curses.color_pair(3)),
            (_t("detail.allow") + ":", "", 0),
        ]
        for a in perms.get("allow", []) or [_t("label.none")]:
            a_str = str(a)
            is_risky = "Bash" in a_str and ("(" in a_str)
            rows.append(("", "  + " + a_str,
                         curses.color_pair(3) if is_risky else curses.color_pair(2)))
        rows.append((_t("detail.deny") + ":", "", 0))
        for d in perms.get("deny", []) or [_t("label.none")]:
            rows.append(("", "  - " + str(d), curses.color_pair(4)))

        extras = {k: v for k, v in env.items() if k not in {
            "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN",
            "ANTHROPIC_BASE_URL", "ANTHROPIC_MODEL",
            "ANTHROPIC_SMALL_FAST_MODEL",
            "CLAUDE_CODE_MAX_OUTPUT_TOKENS"
        }}
        if extras:
            rows.append(("", "─" * min(w - 1, 30), curses.A_DIM))
            rows.append((_t("detail.extra_env") + ":", "", 0))
            for k, v in extras.items():
                _sens = {"KEY", "TOKEN", "SECRET", "AUTH"}
                is_s = any(s in k.upper() for s in _sens)
                rows.append(("", f"  {k}={mask_key(v) if is_s else v}", 0))

        for i, (label, value, attr) in enumerate(rows):
            if i >= h - 1:
                break
            if label:
                self.safe_addstr(y + i, x, label[:w],
                                 curses.A_DIM)
                self.safe_addstr(y + i, x + LABEL_WIDTH,
                                 str(value)[:max(0, w - LABEL_WIDTH)], attr)
            else:
                self.safe_addstr(y + i, x, str(value)[:w], attr)
        if len(rows) > h - 1:
            self.safe_addstr(y + h - 1, x + w - 2, "▼", curses.A_DIM)

    def _draw_detail_env(self, y, x, h, w, path, data):
        curses = _curses_import()
        rows = [
            (_t("detail.file") + ":", path.name, 0),
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
                                 curses.A_DIM)
                self.safe_addstr(y + i, x + LABEL_WIDTH,
                                 str(value)[:max(0, w - LABEL_WIDTH)], attr)
            else:
                self.safe_addstr(y + i, x, str(value)[:w], attr)
        if len(rows) > h - 1:
            self.safe_addstr(y + h - 1, x + w - 2, "▼", curses.A_DIM)

    def _draw_detail_codex(self, y, x, h, w, path, data):
        curses = _curses_import()
        auth = data.get("auth", {}) if isinstance(data, dict) else {}
        config = data.get("config", {}) if isinstance(data, dict) else {}

        rows = [
            (_t("detail.file") + ":", path.name, 0),
            ("", "─" * min(w - 1, 30), curses.A_DIM),
            (_t("detail.auth_section"), "", 0),
            (_t("detail.api_key") + ":",
             mask_key(auth.get("OPENAI_API_KEY", "")),
             curses.color_pair(3)),
            ("", "─" * min(w - 1, 30), curses.A_DIM),
            (_t("detail.config_section"), "", 0),
            (_t("detail.model") + ":",
             str(config.get("model", _t("label.default"))), curses.color_pair(1)),
            (_t("detail.provider") + ":",
             str(config.get("model_provider", _t("label.default"))), 0),
            (_t("detail.base_url") + ":",
             str(config.get("base_url", _t("label.default"))), 0),
        ]
        for i, (label, value, attr) in enumerate(rows):
            if i >= h - 1:
                break
            if label:
                self.safe_addstr(y + i, x, label[:w],
                                 curses.A_DIM)
                self.safe_addstr(y + i, x + LABEL_WIDTH,
                                 str(value)[:max(0, w - LABEL_WIDTH)], attr)
            else:
                self.safe_addstr(y + i, x, str(value)[:w], attr)
        if len(rows) > h - 1:
            self.safe_addstr(y + h - 1, x + w - 2, "▼", curses.A_DIM)

    def activate_selected(self):
        if not self.presets:
            return
        p = self.presets[self.selected]
        warn_type, match_name = _analyze_preset_overlap(p)
        if warn_type == "partial":
            self.confirm_action = (
                _t("confirm.partial_match", name=match_name),
                lambda: self._do_activate(p)
            )
        elif warn_type == "none":
            self.confirm_action = (
                _t("confirm.no_match"),
                lambda: self._do_activate(p)
            )
        else:
            self._do_activate(p)

    def _do_activate(self, p):
        try:
            activate(p)
            self.update_active()
            self.set_message(_t("msg.activated", name=p.stem),
                             "success")
        except Exception as e:
            self.set_message(_t("msg.activation_failed", error=str(e)), "error")

    def edit_selected(self):
        if not self.presets:
            return
        p = self.presets[self.selected]
        open_editor(p)
        self.refresh()
        self.set_message(_t("msg.edited", name=p.stem), "info")

    def new_preset(self):
        self.input_mode = MODE_NEW
        app = _app()
        ext = _preset_ext(app)
        self.input_prompt = _t("prompt.new_name", ext=ext)
        self.input_buffer = ""

    def duplicate_selected(self):
        if not self.presets:
            return
        self.input_mode = MODE_DUP
        self.input_prompt = _t("prompt.dup_as")
        self.input_buffer = self.presets[self.selected].stem + "-copy"

    def rename_selected(self):
        if not self.presets:
            return
        self.input_mode = MODE_RENAME
        self.input_prompt = _t("prompt.rename_to")
        self.input_buffer = self.presets[self.selected].stem

    def backup_live_config(self):
        self.input_mode = MODE_BACKUP
        app = _app()
        ext = _preset_ext(app)
        self.input_prompt = _t("prompt.backup_as", ext=ext)
        self.input_buffer = ""

    def delete_selected(self):
        if not self.presets:
            return
        p = self.presets[self.selected]
        self.confirm_action = (
            _t("confirm.delete_preset", name=p.stem),
            lambda: self._do_delete(p)
        )

    def _do_delete(self, p):
        try:
            p.unlink()
            self.refresh()
            self.set_message(_t("msg.deleted", name=p.stem), "warn")
        except Exception as e:
            self.set_message(_t("msg.delete_failed", error=str(e)), "error")

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
            self.set_message(_t("msg.opened", dir=str(app.presets_dir)), "info")
        except Exception as e:
            self.set_message(_t("msg.open_failed", error=str(e)), "error")

    def open_help(self):
        """Show keyboard shortcuts help overlay."""
        curses = _curses_import()
        all_shortcuts = [
            (_t("help.navigation"), [
                ("↑/↓/j/k", _t("hint.move")),
                ("Enter", _t("hint.activate")),
                ("Tab", _t("hint.app")),
                ("q", _t("hint.quit")),
            ]),
            (_t("help.actions"), [
                ("e", _t("hint.edit")),
                ("n", _t("hint.new")),
                ("d", _t("hint.dup")),
                ("R", _t("hint.rename")),
                ("D", _t("hint.delete")),
                ("B", _t("hint.backup_live")),
            ]),
            (_t("help.view_search"), [
                ("/", _t("hint.filter")),
                ("=", _t("hint.diff")),
                ("b", _t("hint.backups")),
                ("r", _t("hint.reload")),
                ("o", _t("hint.finder")),
            ]),
            (_t("help.tools"), [
                ("p", _t("hint.presets")),
                ("m", _t("hint.mcp")),
                ("?", _t("hint.help")),
            ]),
        ]
        while True:
            self.stdscr.erase()
            h, w = self.stdscr.getmaxyx()
            title = " " + _t("help.title") + " "
            self.safe_addstr(0, 0, title.center(w),
                             curses.color_pair(1) | curses.A_BOLD | curses.A_REVERSE)
            row = 2
            for section, items in all_shortcuts:
                if row >= h - 1:
                    break
                self.safe_addstr(row, 4, section, curses.A_BOLD | curses.A_UNDERLINE)
                row += 1
                for key, desc in items:
                    if row >= h - 1:
                        break
                    self.safe_addstr(row, 6, key.ljust(8), curses.color_pair(7) | curses.A_BOLD)
                    self.safe_addstr(row, 16, desc, curses.A_DIM)
                    row += 1
                row += 1  # gap between sections
            self.safe_addstr(h - 1, 0, (" " + _t("screen.help_footer"))[:w - 1], curses.A_DIM)
            self.stdscr.refresh()
            key = self.stdscr.getch()
            if key in (27, ord('q'), ord('?')):
                break

    def switch_app(self, app_name):
        global _cur_app_name
        _cur_app_name = app_name
        self._detail_cache.clear()
        self.refresh()
        self.update_active()
        self.set_message(_t("msg.switched", app=APPS[app_name].label), "info")

    def handle_input(self, key):
        curses = _curses_import()
        app = _app()
        if key in (10, 13):
            name = self.input_buffer.strip()
            if name:
                try:
                    target = _preset_path_for_name(app, name)
                except ValueError:
                    self.set_message(_t("msg.invalid_name"), "error")
                    return
                if target.exists():
                    self.set_message(_t("msg.already_exists", name=name), "error")
                    return
                if self.input_mode == MODE_NEW:
                    _write_preset_file(target, app.default_template, app)
                    _chmod600(target)
                    self.refresh()
                    self._select_by_path(target)
                    open_editor(target)
                    self.set_message(_t("msg.created", name=name), "success")
                elif self.input_mode == MODE_DUP:
                    src = self.presets[self.selected]
                    _atomic_write(target, src.read_text())
                    self.refresh()
                    self._select_by_path(target)
                    self.set_message(_t("msg.duplicated", name=name), "success")
                elif self.input_mode == MODE_RENAME:
                    src = self.presets[self.selected]
                    src.rename(target)
                    _chmod600(target)
                    self.refresh()
                    self._select_by_path(target)
                    self.set_message(_t("msg.renamed", name=name), "success")
                elif self.input_mode == MODE_BACKUP:
                    try:
                        target = backup_live_as_preset(name)
                        self.refresh()
                        self._select_by_path(target)
                        self.update_active()
                        self.set_message(_t("msg.backed_up_live", name=name), "success")
                    except Exception as e:
                        self.set_message(_t("msg.backup_live_failed", error=str(e)), "error")
            self.input_mode = None
            self.input_buffer = ""
        elif key == 27:
            self.input_mode = None
            self.input_buffer = ""
            self.set_message(_t("msg.cancelled"), "info")
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            self.input_buffer = self.input_buffer[:-1]
        elif 32 <= key < 127:
            self.input_buffer += chr(key)

    def _mouse_dispatch(self, key):
        if key in ("↑↓/jk",):
            return
        if key == "Enter":
            self.activate_selected()
            self.update_active()
        elif key == "e":
            self.edit_selected()
        elif key == "n":
            self.new_preset()
        elif key == "d":
            self.duplicate_selected()
        elif key == "R":
            self.rename_selected()
        elif key == "D":
            self.delete_selected()
        elif key == "/":
            self.enter_search()
        elif key == "=":
            self.diff_selected()
        elif key == "b":
            self.open_backups()
        elif key == "B":
            self.backup_live_config()
        elif key == "r":
            self.refresh()
            self.update_active()
            self.set_message("Reloaded", "info")
        elif key == "o":
            self.open_dir()
        elif key == "Tab":
            idx = APP_ORDER.index(_cur_app_name)
            self.switch_app(APP_ORDER[(idx + 1) % len(APP_ORDER)])
        elif key == "p":
            self.open_provider_picker()
        elif key == "m":
            self.open_mcp_manager()
        elif key == "?":
            self.open_help()
        elif key == "q":
            self._mouse_quit = True

    def handle_mouse(self):
        curses = _curses_import()
        try:
            _, mx, my, _, bstate = curses.getmouse()
        except Exception:
            return

        if bstate & curses.BUTTON1_CLICKED:
            pass
        elif hasattr(curses, "BUTTON4_PRESSED") and (bstate & curses.BUTTON4_PRESSED):
            if self.selected > 0:
                self.selected -= 1
            return
        elif hasattr(curses, "BUTTON5_PRESSED") and (bstate & curses.BUTTON5_PRESSED):
            if self.selected < len(self.presets) - 1:
                self.selected += 1
            return
        else:
            return

        h, w = self.stdscr.getmaxyx()

        # Tab clicks (row 1)
        if my == 1:
            for _row, xs, xe, app_name in self._tab_hitboxes:
                if xs <= mx < xe:
                    self.switch_app(app_name)
                    return

        # Key hint clicks (bottom rows)
        for row, xs, xe, key in self._key_hitboxes:
            if my == row and xs <= mx < xe:
                self._mouse_dispatch(key)
                return

        # Preset list clicks
        if self.presets:
            fb = 1 if self.filter_text else 0
            header_row = 4 + fb
            list_h = h - 6 - fb
            list_w = max(MIN_LIST_W, w // 3)
            visible = min(list_h - 1, len(self.presets) - self.scroll)
            if 0 <= mx < list_w and header_row + 1 <= my < header_row + 1 + visible:
                idx = self.scroll + (my - (header_row + 1))
                if 0 <= idx < len(self.presets):
                    self.selected = idx
                    self.activate_selected()
                    self.update_active()

    def handle_confirm(self, key):
        _, action = self.confirm_action
        if key in (ord('y'), ord('Y')):
            action()
        else:
            self.set_message(_t("msg.cancelled"), "info")
        self.confirm_action = None

    def diff_selected(self):
        if not self.presets:
            return
        show_diff(self.presets[self.selected], in_curses=True)
        self.set_message(_t("msg.diff_viewed"), "info")

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
            self.set_message(_t("msg.filter_cleared"), "info")
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
            self.set_message(_t("msg.no_backups"), "warn")
            return
        sel = 0
        scroll = 0
        while True:
            self.stdscr.erase()
            h, w = self.stdscr.getmaxyx()
            title = " " + _t("screen.backups_title") + " "
            self.safe_addstr(0, 0, title.center(w),
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
                             " " + _t("screen.backups_footer", count=len(backups))[:w - 1],
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
                    _t("confirm.restore_backup", name=b.name),
                    lambda bp=b: self._do_restore(bp)
                )
                break
        self.refresh()
        self.update_active()

    def _do_restore(self, backup_path):
        try:
            restore_backup(backup_path)
            self.set_message(_t("msg.restored", name=backup_path.name), "success")
        except Exception as e:
            self.set_message(_t("msg.restore_failed", error=str(e)), "error")

    # ── Provider Preset Picker ──────────────────────────────────────

    def open_provider_picker(self):
        curses = _curses_import()
        providers = BUILTIN_PROVIDERS.get(_cur_app_name, {})
        if not providers:
            self.set_message(_t("msg.no_providers"), "warn")
            return
        categories = list(providers.keys())
        cat_sel = 0
        item_sel = 0
        while True:
            self.stdscr.erase()
            h, w = self.stdscr.getmaxyx()
            title = " " + _t("screen.providers_title") + " "
            self.safe_addstr(0, 0, title.center(w),
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
                             " " + _t("screen.providers_footer")[:w - 1],
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
        if target.exists():
            self.set_message(_t("msg.import_exists", name=name), "error")
            return
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
        self.set_message(_t("msg.imported", name=name), "success")

    # ── MCP Manager ──────────────────────────────────────────────────

    def open_mcp_manager(self):
        curses = _curses_import()
        if _cur_app_name != "claude":
            self.set_message(_t("msg.mcp_claude_only"), "warn")
            return
        app = _app()
        try:
            settings = _read_settings(app) if app.settings_file.exists() else {}
        except Exception as e:
            self.set_message(_t("msg.cannot_read", error=str(e)), "error")
            return
        mcp_servers = settings.get("mcpServers", {}) if isinstance(settings, dict) else {}
        names = list(mcp_servers.keys())
        sel = 0
        while True:
            self.stdscr.erase()
            h, w = self.stdscr.getmaxyx()
            title = " " + _t("screen.mcp_title") + " "
            self.safe_addstr(0, 0, title.center(w),
                             curses.color_pair(1) | curses.A_BOLD | curses.A_REVERSE)
            if not names:
                self.safe_addstr(2, 2, _t("screen.mcp_empty"), curses.A_DIM)
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
                             " " + _t("screen.mcp_footer")[:w - 1],
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
                    self.set_message(_t("msg.mcp_added", name=new_cfg["name"]), "success")
            elif key == ord('D') and names:
                deleted = names[sel]
                del mcp_servers[deleted]
                names = list(mcp_servers.keys())
                sel = min(sel, max(0, len(names) - 1))
                settings["mcpServers"] = mcp_servers
                _atomic_write(app.settings_file,
                              json.dumps(settings, indent=2, ensure_ascii=False))
                _chmod600(app.settings_file)
                self.set_message(_t("msg.mcp_deleted", name=deleted), "warn")

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
            (_t("prompt.mcp_name"), "name"),
            (_t("prompt.mcp_command"), "command"),
            (_t("prompt.mcp_args"), "args_str"),
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

            if key == curses.KEY_MOUSE:
                if not self.in_search and not self.input_mode and not self.confirm_action:
                    self.handle_mouse()
                    if self._mouse_quit:
                        break
                continue

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
            elif key == ord('B'):
                self.backup_live_config()
            elif key == ord('r'):
                self.refresh()
                self.update_active()
                self.set_message(_t("msg.reloaded"), "info")
            elif key == ord('o'):
                self.open_dir()
            elif key == ord('\t'):
                idx = APP_ORDER.index(_cur_app_name)
                self.switch_app(APP_ORDER[(idx + 1) % len(APP_ORDER)])
            elif key == ord('p'):
                self.open_provider_picker()
            elif key == ord('m'):
                self.open_mcp_manager()
            elif key == ord('?'):
                self.open_help()
            elif key == curses.KEY_RESIZE:
                pass


# ── Translations ──────────────────────────────────────────────────────

L10N = {
    "en": {
        # TUI labels
        "label.title": "clap — Multi-Tool Profile Manager",
        "label.active": "Active",
        "label.target": "Target",
        "label.filter": "Filter",
        "label.presets_hdr": "Presets",
        "label.details_hdr": "Details",
        "label.no_presets": "(no presets, press 'n' to create)",
        "label.none": "(none)",
        "label.default": "(default)",
        "label.too_small": "Terminal too small (need >= {w}x{h})",
        # Key hints
        "hint.move": "Move",
        "hint.activate": "Activate",
        "hint.edit": "Edit",
        "hint.new": "New",
        "hint.dup": "Dup",
        "hint.rename": "Rename",
        "hint.delete": "Delete",
        "hint.filter": "Filter",
        "hint.diff": "Diff",
        "hint.backups": "Backups",
        "hint.backup_live": "Backup Live",
        "hint.reload": "Reload",
        "hint.finder": "Finder",
        "hint.app": "App",
        "hint.presets": "Presets",
        "hint.mcp": "MCP",
        "hint.quit": "Quit",
        "hint.help": "Help",
        # Detail panel
        "detail.file": "File",
        "detail.api_key": "API_KEY",
        "detail.auth_token": "AUTH_TOKEN",
        "detail.base_url": "Base URL",
        "detail.model": "Model",
        "detail.small_model": "Small Model",
        "detail.max_output": "Max Output",
        "detail.mode": "Mode",
        "detail.allow": "Allow",
        "detail.deny": "Deny",
        "detail.extra_env": "Extra Env",
        "detail.auth_section": "[Auth]",
        "detail.config_section": "[Config]",
        "detail.provider": "Provider",
        # Messages
        "msg.activated": "Activated: {name}  (previous backed up)",
        "msg.activation_failed": "Activation failed: {error}",
        "msg.edited": "Edited: {name}",
        "msg.deleted": "Deleted: {name}",
        "msg.delete_failed": "Delete failed: {error}",
        "msg.created": "Created: {name}",
        "msg.duplicated": "Duplicated to: {name}",
        "msg.renamed": "Renamed to: {name}",
        "msg.cancelled": "Cancelled",
        "msg.reloaded": "Reloaded",
        "msg.switched": "Switched to {app}",
        "msg.invalid_name": "Invalid preset name",
        "msg.already_exists": "'{name}' already exists",
        "msg.opened": "Opened {dir}",
        "msg.open_failed": "Open dir failed: {error}",
        "msg.diff_viewed": "Diff viewed",
        "msg.filter_cleared": "Filter cleared",
        "msg.no_backups": "No backups available",
        "msg.no_live_config": "No live config found",
        "msg.backed_up_live": "Saved live config as preset: {name}",
        "msg.backup_live_failed": "Backup failed: {error}",
        "msg.restored": "Restored: {name}",
        "msg.restore_failed": "Restore failed: {error}",
        "msg.no_providers": "No built-in providers for this app",
        "msg.import_exists": "'{name}' already exists — delete it first",
        "msg.imported": "Imported '{name}' — fill in your API key",
        "msg.mcp_claude_only": "MCP management is only available for Claude Code",
        "msg.cannot_read": "Cannot read settings: {error}",
        "msg.mcp_added": "Added MCP server: {name}",
        "msg.mcp_deleted": "Deleted MCP server: {name}",
        "msg.update_failed": "Update failed: {error}",
        "msg.already_up_to_date": "Already up to date (v{version}).",
        "msg.updated": "Updated v{old} → v{new}",
        "msg.updated_ok": "Updated successfully.",
        "msg.warning_chmod": "Warning: could not chmod 600 {path}: {error}",
        "msg.warning_backup_cleanup": "Warning: backup cleanup failed: {error}",
        "msg.error_launching_editor": "Error launching editor: {error}",
        "msg.press_enter": "Press Enter to continue...",
        "msg.error_reading_preset": "Error reading preset: {error}",
        "msg.no_differences": "No differences.",
        # Confirm
        "confirm.partial_match": "Shares provider with '{name}' but different credentials — proceed anyway? (y/N) ",
        "confirm.no_match": "New provider — save current config as a preset before losing it? Proceed anyway? (y/N) ",
        "confirm.delete_preset": "Delete preset '{name}'? press y to confirm, any other to cancel ",
        "confirm.restore_backup": "Restore '{name}'? press y to confirm, any other to cancel ",
        # Sub-screens
        "screen.backups_title": "Backups (Enter=restore, Esc=back)",
        "screen.backups_footer": "{count} backups — ↑↓/jk move  Enter restore  Esc back",
        "screen.providers_title": "Built-in Providers (Enter=import, Esc=back)",
        "screen.providers_footer": "←→: category  ↑↓: provider  Enter: import  Esc: back",
        "screen.mcp_title": "MCP Servers (a=add, D=delete, Esc=back)",
        "screen.mcp_empty": "(no MCP servers configured)",
        "screen.mcp_footer": "↑↓: select  a: add  D: delete  Esc: back",
        # Input prompts
        "prompt.new_name": "New preset name (without {ext}): ",
        "prompt.backup_as": "Backup live config as preset (without {ext}): ",
        "prompt.dup_as": "Duplicate as: ",
        "prompt.rename_to": "Rename to: ",
        "prompt.mcp_name": "MCP server name (e.g. fetch): ",
        "prompt.mcp_command": "Command (e.g. uvx): ",
        "prompt.mcp_args": "Args (space-separated, e.g. mcp-server-fetch): ",
        # CLI
        "cli.warning_partial1": "Warning: Shares provider with '{name}' but has different credentials.",
        "cli.warning_partial2": "Your current config may belong to a different account of the same provider.",
        "cli.warning_none1": "Warning: No matching provider found in stored presets.",
        "cli.warning_none2": "Your current config will be lost. Consider saving it as a new preset first.",
        "cli.proceed": "Proceed anyway? (y/N): ",
        "cli.cancelled": "Cancelled.",
        "cli.activated": "Activated: {name}",
        "cli.unknown": "(unknown)",
        "cli.not_found": "Preset not found: {name}",
        "cli.invalid_preset": "Invalid preset name: {name}",
        "cli.preset_exists": "Preset already exists: {name}",
        "cli.no_live_config": "No live config found.",
        "cli.backed_up_live": "Saved live config as preset: {name}",
        "cli.backup_failed": "Backup failed: {error}",
        "cli.backup_usage": "Usage: clap backup <name>",
        "cli.no_backups": "No backups found.",
        "cli.invalid_backup": "Invalid backup name: {name}",
        "cli.backup_not_found": "Backup not found: {name}",
        "cli.restored": "Restored: {name}",
        "cli.version": "clap v{version}",
        "cli.unsupported_lang": "Unsupported language: {code}. Available: zh-CN, zh-TW, ja, en",
        "cli.lang_set": "Language set to {code}",
        "cli.current_lang": "Current language: {code} ({label})",
        "cli.lang_en": "English",
        "cli.lang_zhcn": "简体中文",
        "cli.lang_zhtw": "繁體中文",
        "cli.lang_ja": "日本語",
        # Help panel
        "screen.help_footer": "Esc/q/? — close",
        "msg.lang_save_failed": "Failed to save language setting: {error}",
        "help.title": "Help — Keyboard Shortcuts",
        "help.navigation": "Navigation",
        "help.actions": "Actions",
        "help.view_search": "View & Search",
        "help.tools": "Tools",
    },
    "zh-CN": {
        "label.title": "clap — 多工具配置管理器",
        "label.active": "当前",
        "label.target": "目标",
        "label.filter": "筛选",
        "label.presets_hdr": "预设",
        "label.details_hdr": "详情",
        "label.no_presets": "（无预设，按 'n' 新建）",
        "label.none": "（无）",
        "label.default": "（默认）",
        "label.too_small": "终端窗口过小（需要 >= {w}x{h}）",
        "hint.move": "移动",
        "hint.activate": "激活",
        "hint.edit": "编辑",
        "hint.new": "新建",
        "hint.dup": "复制",
        "hint.rename": "重命名",
        "hint.delete": "删除",
        "hint.filter": "筛选",
        "hint.diff": "对比",
        "hint.backups": "备份",
        "hint.backup_live": "备份当前",
        "hint.reload": "刷新",
        "hint.finder": "打开",
        "hint.app": "切换",
        "hint.presets": "预设库",
        "hint.mcp": "MCP",
        "hint.quit": "退出",
        "hint.help": "帮助",
        "detail.file": "文件",
        "detail.api_key": "API_KEY",
        "detail.auth_token": "AUTH_TOKEN",
        "detail.base_url": "Base URL",
        "detail.model": "模型",
        "detail.small_model": "小型模型",
        "detail.max_output": "最大输出",
        "detail.mode": "模式",
        "detail.allow": "允许",
        "detail.deny": "拒绝",
        "detail.extra_env": "额外环境变量",
        "detail.auth_section": "[认证]",
        "detail.config_section": "[配置]",
        "detail.provider": "供应商",
        "msg.activated": "已激活：{name}（旧配置已备份）",
        "msg.activation_failed": "激活失败：{error}",
        "msg.edited": "已编辑：{name}",
        "msg.deleted": "已删除：{name}",
        "msg.delete_failed": "删除失败：{error}",
        "msg.created": "已创建：{name}",
        "msg.duplicated": "已复制为：{name}",
        "msg.renamed": "已重命名为：{name}",
        "msg.cancelled": "已取消",
        "msg.reloaded": "已刷新",
        "msg.switched": "已切换到 {app}",
        "msg.invalid_name": "预设名称无效",
        "msg.already_exists": "'{name}' 已存在",
        "msg.opened": "已打开 {dir}",
        "msg.open_failed": "打开文件夹失败：{error}",
        "msg.diff_viewed": "已查看对比",
        "msg.filter_cleared": "筛选已清除",
        "msg.no_backups": "暂无备份",
        "msg.no_live_config": "未找到当前配置",
        "msg.backed_up_live": "已将当前配置保存为预设：{name}",
        "msg.backup_live_failed": "备份失败：{error}",
        "msg.restored": "已恢复：{name}",
        "msg.restore_failed": "恢复失败：{error}",
        "msg.no_providers": "此工具无内置供应商预设",
        "msg.import_exists": "'{name}' 已存在 — 请先删除",
        "msg.imported": "已导入 '{name}' — 请填入 API key",
        "msg.mcp_claude_only": "MCP 管理仅适用于 Claude Code",
        "msg.cannot_read": "无法读取配置：{error}",
        "msg.mcp_added": "已添加 MCP 服务器：{name}",
        "msg.mcp_deleted": "已删除 MCP 服务器：{name}",
        "msg.update_failed": "更新失败：{error}",
        "msg.already_up_to_date": "已是最新版本（v{version}）。",
        "msg.updated": "已更新 v{old} → v{new}",
        "msg.updated_ok": "更新成功。",
        "msg.warning_chmod": "警告：无法 chmod 600 {path}：{error}",
        "msg.warning_backup_cleanup": "警告：备份清理失败：{error}",
        "msg.error_launching_editor": "启动编辑器失败：{error}",
        "msg.press_enter": "按 Enter 继续...",
        "msg.error_reading_preset": "读取预设出错：{error}",
        "msg.no_differences": "无差异。",
        "confirm.partial_match": "与预设 '{name}' 共享供应商但凭据不同 — 是否继续？(y/N) ",
        "confirm.no_match": "未找到匹配的供应商 — 建议先将当前配置保存为新预设。是否继续？(y/N) ",
        "confirm.delete_preset": "删除预设 '{name}'？按 y 确认，其他键取消 ",
        "confirm.restore_backup": "恢复备份 '{name}'？按 y 确认，其他键取消 ",
        "screen.backups_title": "备份（Enter=恢复, Esc=返回）",
        "screen.backups_footer": "{count} 个备份 — ↑↓/jk 移动  Enter 恢复  Esc 返回",
        "screen.providers_title": "内置供应商预设（Enter=导入, Esc=返回）",
        "screen.providers_footer": "←→: 分类  ↑↓: 供应商  Enter: 导入  Esc: 返回",
        "screen.mcp_title": "MCP 服务器（a=添加, D=删除, Esc=返回）",
        "screen.mcp_empty": "（未配置 MCP 服务器）",
        "screen.mcp_footer": "↑↓: 选择  a: 添加  D: 删除  Esc: 返回",
        "prompt.new_name": "新建预设名称（不含 {ext}）：",
        "prompt.backup_as": "将当前配置备份为预设（不含 {ext}）：",
        "prompt.dup_as": "复制为：",
        "prompt.rename_to": "重命名为：",
        "prompt.mcp_name": "MCP 服务器名称（例如 fetch）：",
        "prompt.mcp_command": "命令（例如 uvx）：",
        "prompt.mcp_args": "参数（空格分隔，例如 mcp-server-fetch）：",
        "cli.warning_partial1": "警告：与预设 '{name}' 共享供应商但凭据不同。",
        "cli.warning_partial2": "当前配置可能属于同一供应商的不同账户。",
        "cli.warning_none1": "警告：在已存储的预设中未找到匹配的供应商。",
        "cli.warning_none2": "当前配置将丢失，建议先保存为新预设。",
        "cli.proceed": "是否继续？(y/N)：",
        "cli.cancelled": "已取消。",
        "cli.activated": "已激活：{name}",
        "cli.unknown": "（未知）",
        "cli.not_found": "预设未找到：{name}",
        "cli.invalid_preset": "预设名称无效：{name}",
        "cli.preset_exists": "预设已存在：{name}",
        "cli.no_live_config": "未找到当前配置。",
        "cli.backed_up_live": "已将当前配置保存为预设：{name}",
        "cli.backup_failed": "备份失败：{error}",
        "cli.backup_usage": "用法：clap backup <name>",
        "cli.no_backups": "暂无备份。",
        "cli.invalid_backup": "备份名称无效：{name}",
        "cli.backup_not_found": "备份未找到：{name}",
        "cli.restored": "已恢复：{name}",
        "cli.version": "clap v{version}",
        "cli.unsupported_lang": "不支持的语言：{code}。可用：zh-CN, zh-TW, ja, en",
        "cli.lang_set": "语言已设置为 {code}",
        "cli.current_lang": "当前语言：{code}（{label}）",
        "cli.lang_en": "English",
        "cli.lang_zhcn": "简体中文",
        "cli.lang_zhtw": "繁體中文",
        "cli.lang_ja": "日本語",
        "screen.help_footer": "Esc/q/? — 关闭",
        "msg.lang_save_failed": "保存语言设置失败：{error}",
        "help.title": "帮助 — 快捷键",
        "help.navigation": "导航",
        "help.actions": "操作",
        "help.view_search": "视图 & 搜索",
        "help.tools": "工具",
    },
    "zh-TW": {
        "label.title": "clap — 多工具設定管理器",
        "label.active": "目前",
        "label.target": "目標",
        "label.filter": "篩選",
        "label.presets_hdr": "預設",
        "label.details_hdr": "詳情",
        "label.no_presets": "（無預設，按 'n' 新增）",
        "label.none": "（無）",
        "label.default": "（預設）",
        "label.too_small": "終端機視窗過小（需要 >= {w}x{h}）",
        "hint.move": "移動",
        "hint.activate": "啟用",
        "hint.edit": "編輯",
        "hint.new": "新增",
        "hint.dup": "複製",
        "hint.rename": "重新命名",
        "hint.delete": "刪除",
        "hint.filter": "篩選",
        "hint.diff": "比對",
        "hint.backups": "備份",
        "hint.backup_live": "備份目前",
        "hint.reload": "重新整理",
        "hint.finder": "開啟",
        "hint.app": "切換",
        "hint.presets": "預設庫",
        "hint.mcp": "MCP",
        "hint.quit": "離開",
        "hint.help": "幫助",
        "detail.file": "檔案",
        "detail.api_key": "API_KEY",
        "detail.auth_token": "AUTH_TOKEN",
        "detail.base_url": "Base URL",
        "detail.model": "模型",
        "detail.small_model": "小型模型",
        "detail.max_output": "最大輸出",
        "detail.mode": "模式",
        "detail.allow": "允許",
        "detail.deny": "拒絕",
        "detail.extra_env": "額外環境變數",
        "detail.auth_section": "[認證]",
        "detail.config_section": "[設定]",
        "detail.provider": "供應商",
        "msg.activated": "已啟用：{name}（舊設定已備份）",
        "msg.activation_failed": "啟用失敗：{error}",
        "msg.edited": "已編輯：{name}",
        "msg.deleted": "已刪除：{name}",
        "msg.delete_failed": "刪除失敗：{error}",
        "msg.created": "已建立：{name}",
        "msg.duplicated": "已複製為：{name}",
        "msg.renamed": "已重新命名為：{name}",
        "msg.cancelled": "已取消",
        "msg.reloaded": "已重新整理",
        "msg.switched": "已切換至 {app}",
        "msg.invalid_name": "預設名稱無效",
        "msg.already_exists": "'{name}' 已存在",
        "msg.opened": "已開啟 {dir}",
        "msg.open_failed": "開啟資料夾失敗：{error}",
        "msg.diff_viewed": "已檢視比對",
        "msg.filter_cleared": "篩選已清除",
        "msg.no_backups": "暫無備份",
        "msg.no_live_config": "未找到目前設定",
        "msg.backed_up_live": "已將目前設定儲存為預設：{name}",
        "msg.backup_live_failed": "備份失敗：{error}",
        "msg.restored": "已復原：{name}",
        "msg.restore_failed": "復原失敗：{error}",
        "msg.no_providers": "此工具無內建供應商預設",
        "msg.import_exists": "'{name}' 已存在 — 請先刪除",
        "msg.imported": "已匯入 '{name}' — 請填入 API key",
        "msg.mcp_claude_only": "MCP 管理僅適用於 Claude Code",
        "msg.cannot_read": "無法讀取設定：{error}",
        "msg.mcp_added": "已新增 MCP 伺服器：{name}",
        "msg.mcp_deleted": "已刪除 MCP 伺服器：{name}",
        "msg.update_failed": "更新失敗：{error}",
        "msg.already_up_to_date": "已是最新版本（v{version}）。",
        "msg.updated": "已更新 v{old} → v{new}",
        "msg.updated_ok": "更新成功。",
        "msg.warning_chmod": "警告：無法 chmod 600 {path}：{error}",
        "msg.warning_backup_cleanup": "警告：備份清理失敗：{error}",
        "msg.error_launching_editor": "啟動編輯器失敗：{error}",
        "msg.press_enter": "按 Enter 繼續...",
        "msg.error_reading_preset": "讀取預設出錯：{error}",
        "msg.no_differences": "無差異。",
        "confirm.partial_match": "與預設 '{name}' 共享供應商但憑據不同 — 是否繼續？(y/N) ",
        "confirm.no_match": "未找到匹配的供應商 — 建議先將目前設定儲存為新預設。是否繼續？(y/N) ",
        "confirm.delete_preset": "刪除預設 '{name}'？按 y 確認，其他鍵取消 ",
        "confirm.restore_backup": "復原備份 '{name}'？按 y 確認，其他鍵取消 ",
        "screen.backups_title": "備份（Enter=復原, Esc=返回）",
        "screen.backups_footer": "{count} 個備份 — ↑↓/jk 移動  Enter 復原  Esc 返回",
        "screen.providers_title": "內建供應商預設（Enter=匯入, Esc=返回）",
        "screen.providers_footer": "←→: 分類  ↑↓: 供應商  Enter: 匯入  Esc: 返回",
        "screen.mcp_title": "MCP 伺服器（a=新增, D=刪除, Esc=返回）",
        "screen.mcp_empty": "（未設定 MCP 伺服器）",
        "screen.mcp_footer": "↑↓: 選擇  a: 新增  D: 刪除  Esc: 返回",
        "prompt.new_name": "新增預設名稱（不含 {ext}）：",
        "prompt.backup_as": "將目前設定備份為預設（不含 {ext}）：",
        "prompt.dup_as": "複製為：",
        "prompt.rename_to": "重新命名為：",
        "prompt.mcp_name": "MCP 伺服器名稱（例如 fetch）：",
        "prompt.mcp_command": "指令（例如 uvx）：",
        "prompt.mcp_args": "參數（空格分隔，例如 mcp-server-fetch）：",
        "cli.warning_partial1": "警告：與預設 '{name}' 共享供應商但憑據不同。",
        "cli.warning_partial2": "目前設定可能屬於同一供應商的不同帳戶。",
        "cli.warning_none1": "警告：在已儲存的預設中未找到匹配的供應商。",
        "cli.warning_none2": "目前設定將遺失，建議先儲存為新預設。",
        "cli.proceed": "是否繼續？(y/N)：",
        "cli.cancelled": "已取消。",
        "cli.activated": "已啟用：{name}",
        "cli.unknown": "（未知）",
        "cli.not_found": "預設未找到：{name}",
        "cli.invalid_preset": "預設名稱無效：{name}",
        "cli.preset_exists": "預設已存在：{name}",
        "cli.no_live_config": "未找到目前設定。",
        "cli.backed_up_live": "已將目前設定儲存為預設：{name}",
        "cli.backup_failed": "備份失敗：{error}",
        "cli.backup_usage": "用法：clap backup <name>",
        "cli.no_backups": "暫無備份。",
        "cli.invalid_backup": "備份名稱無效：{name}",
        "cli.backup_not_found": "備份未找到：{name}",
        "cli.restored": "已復原：{name}",
        "cli.version": "clap v{version}",
        "cli.unsupported_lang": "不支援的語言：{code}。可用：zh-CN, zh-TW, ja, en",
        "cli.lang_set": "語言已設定為 {code}",
        "cli.current_lang": "目前語言：{code}（{label}）",
        "cli.lang_en": "English",
        "cli.lang_zhcn": "简体中文",
        "cli.lang_zhtw": "繁體中文",
        "cli.lang_ja": "日本語",
        "screen.help_footer": "Esc/q/? — 關閉",
        "msg.lang_save_failed": "儲存語言設定失敗：{error}",
        "help.title": "幫助 — 快速鍵",
        "help.navigation": "導覽",
        "help.actions": "操作",
        "help.view_search": "檢視 & 搜尋",
        "help.tools": "工具",
    },
    "ja": {
        "label.title": "clap — マルチツールプロファイルマネージャー",
        "label.active": "現在",
        "label.target": "ターゲット",
        "label.filter": "フィルタ",
        "label.presets_hdr": "プリセット",
        "label.details_hdr": "詳細",
        "label.no_presets": "（プリセットなし、'n' で新規作成）",
        "label.none": "（なし）",
        "label.default": "（デフォルト）",
        "label.too_small": "端末が小さすぎます（{w}x{h} 以上必要）",
        "hint.move": "移動",
        "hint.activate": "有効化",
        "hint.edit": "編集",
        "hint.new": "新規",
        "hint.dup": "複製",
        "hint.rename": "名前変更",
        "hint.delete": "削除",
        "hint.filter": "フィルタ",
        "hint.diff": "比較",
        "hint.backups": "バックアップ",
        "hint.backup_live": "現設定保存",
        "hint.reload": "再読み込み",
        "hint.finder": "開く",
        "hint.app": "切替",
        "hint.presets": "プリセット",
        "hint.mcp": "MCP",
        "hint.quit": "終了",
        "hint.help": "ヘルプ",
        "detail.file": "ファイル",
        "detail.api_key": "API_KEY",
        "detail.auth_token": "AUTH_TOKEN",
        "detail.base_url": "Base URL",
        "detail.model": "モデル",
        "detail.small_model": "小型モデル",
        "detail.max_output": "最大出力",
        "detail.mode": "モード",
        "detail.allow": "許可",
        "detail.deny": "拒否",
        "detail.extra_env": "追加環境変数",
        "detail.auth_section": "[認証]",
        "detail.config_section": "[設定]",
        "detail.provider": "プロバイダー",
        "msg.activated": "有効化: {name}（旧設定はバックアップ済み）",
        "msg.activation_failed": "有効化失敗: {error}",
        "msg.edited": "編集済み: {name}",
        "msg.deleted": "削除済み: {name}",
        "msg.delete_failed": "削除失敗: {error}",
        "msg.created": "作成済み: {name}",
        "msg.duplicated": "複製先: {name}",
        "msg.renamed": "名前変更先: {name}",
        "msg.cancelled": "キャンセル",
        "msg.reloaded": "再読み込み完了",
        "msg.switched": "{app} に切り替えました",
        "msg.invalid_name": "無効なプリセット名",
        "msg.already_exists": "'{name}' は既に存在します",
        "msg.opened": "{dir} を開きました",
        "msg.open_failed": "フォルダを開けませんでした: {error}",
        "msg.diff_viewed": "差分を表示しました",
        "msg.filter_cleared": "フィルタをクリアしました",
        "msg.no_backups": "バックアップがありません",
        "msg.no_live_config": "現在の設定が見つかりません",
        "msg.backed_up_live": "現在の設定をプリセットとして保存しました: {name}",
        "msg.backup_live_failed": "バックアップ失敗: {error}",
        "msg.restored": "復元済み: {name}",
        "msg.restore_failed": "復元失敗: {error}",
        "msg.no_providers": "このツールに内蔵プロバイダーはありません",
        "msg.import_exists": "'{name}' は既に存在します — 先に削除してください",
        "msg.imported": "'{name}' をインポートしました — APIキーを入力してください",
        "msg.mcp_claude_only": "MCP管理はClaude Codeのみ対応です",
        "msg.cannot_read": "設定を読み込めません: {error}",
        "msg.mcp_added": "MCPサーバーを追加: {name}",
        "msg.mcp_deleted": "MCPサーバーを削除: {name}",
        "msg.update_failed": "更新失敗: {error}",
        "msg.already_up_to_date": "既に最新バージョンです（v{version}）。",
        "msg.updated": "更新完了 v{old} → v{new}",
        "msg.updated_ok": "更新に成功しました。",
        "msg.warning_chmod": "警告: chmod 600 に失敗 {path}: {error}",
        "msg.warning_backup_cleanup": "警告: バックアップクリーンアップ失敗: {error}",
        "msg.error_launching_editor": "エディタ起動エラー: {error}",
        "msg.press_enter": "Enterを押して続行...",
        "msg.error_reading_preset": "プリセット読み込みエラー: {error}",
        "msg.no_differences": "差分はありません。",
        "confirm.partial_match": "プリセット '{name}' とプロバイダーが同じですが認証情報が異なります — 続行しますか？(y/N) ",
        "confirm.no_match": "一致するプロバイダーが見つかりません — 現在の設定を新しいプリセットとして保存することをお勧めします。続行しますか？(y/N) ",
        "confirm.delete_preset": "プリセット '{name}' を削除しますか？ y で確認、他キーでキャンセル ",
        "confirm.restore_backup": "バックアップ '{name}' を復元しますか？ y で確認、他キーでキャンセル ",
        "screen.backups_title": "バックアップ（Enter=復元, Esc=戻る）",
        "screen.backups_footer": "{count} 件のバックアップ — ↑↓/jk 移動  Enter 復元  Esc 戻る",
        "screen.providers_title": "内蔵プロバイダー（Enter=インポート, Esc=戻る）",
        "screen.providers_footer": "←→: カテゴリ  ↑↓: プロバイダー  Enter: インポート  Esc: 戻る",
        "screen.mcp_title": "MCPサーバー（a=追加, D=削除, Esc=戻る）",
        "screen.mcp_empty": "（MCPサーバー未設定）",
        "screen.mcp_footer": "↑↓: 選択  a: 追加  D: 削除  Esc: 戻る",
        "prompt.new_name": "新規プリセット名（{ext} を除く）：",
        "prompt.backup_as": "現在の設定をプリセットとして保存（{ext} を除く）：",
        "prompt.dup_as": "複製先：",
        "prompt.rename_to": "名前変更先：",
        "prompt.mcp_name": "MCPサーバー名（例: fetch）：",
        "prompt.mcp_command": "コマンド（例: uvx）：",
        "prompt.mcp_args": "引数（スペース区切り、例: mcp-server-fetch）：",
        "cli.warning_partial1": "警告: プリセット '{name}' とプロバイダーが同じですが認証情報が異なります。",
        "cli.warning_partial2": "現在の設定は同一プロバイダーの別アカウントの可能性があります。",
        "cli.warning_none1": "警告: 保存済みプリセットに一致するプロバイダーが見つかりません。",
        "cli.warning_none2": "現在の設定が失われます。先に新規プリセットとして保存することをお勧めします。",
        "cli.proceed": "続行しますか？(y/N): ",
        "cli.cancelled": "キャンセルしました。",
        "cli.activated": "有効化: {name}",
        "cli.unknown": "（不明）",
        "cli.not_found": "プリセットが見つかりません: {name}",
        "cli.invalid_preset": "無効なプリセット名: {name}",
        "cli.preset_exists": "プリセットは既に存在します: {name}",
        "cli.no_live_config": "現在の設定が見つかりません。",
        "cli.backed_up_live": "現在の設定をプリセットとして保存しました: {name}",
        "cli.backup_failed": "バックアップ失敗: {error}",
        "cli.backup_usage": "使い方: clap backup <name>",
        "cli.no_backups": "バックアップがありません。",
        "cli.invalid_backup": "無効なバックアップ名: {name}",
        "cli.backup_not_found": "バックアップが見つかりません: {name}",
        "cli.restored": "復元済み: {name}",
        "cli.version": "clap v{version}",
        "cli.unsupported_lang": "未対応の言語: {code}。利用可能: zh-CN, zh-TW, ja, en",
        "cli.lang_set": "言語を {code} に設定しました",
        "cli.current_lang": "現在の言語: {code}（{label}）",
        "cli.lang_en": "English",
        "cli.lang_zhcn": "简体中文",
        "cli.lang_zhtw": "繁體中文",
        "cli.lang_ja": "日本語",
        "screen.help_footer": "Esc/q/? — 閉じる",
        "msg.lang_save_failed": "言語設定の保存に失敗しました: {error}",
        "help.title": "ヘルプ — キーボードショートカット",
        "help.navigation": "ナビゲーション",
        "help.actions": "操作",
        "help.view_search": "表示 & 検索",
        "help.tools": "ツール",
    },
}


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
        print(_t("msg.update_failed", error=str(e)), file=sys.stderr)
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
        print(_t("msg.already_up_to_date", version=VERSION))
        return

    self_path = Path(sys.argv[0]).resolve()
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tmp:
        tmp.write(new_src)
        tmp_path = Path(tmp.name)
    try:
        os.chmod(tmp_path, 0o755)
        tmp_path.replace(self_path)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise

    if remote_version:
        print(_t("msg.updated", old=VERSION, new=remote_version))
    else:
        print(_t("msg.updated_ok"))


def _check_update():
    """Check GitHub for a newer version. Returns remote version or None.
    Blocking with short timeout (2s). Silently ignores failures."""
    import urllib.request
    url = "https://raw.githubusercontent.com/pterchan/clap/main/clap.py"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=2) as resp:
            content = resp.read(2048).decode("utf-8")
        for line in content.splitlines():
            if line.startswith("VERSION"):
                remote = line.split("=")[1].strip().strip('"').strip("'")
                return remote
    except Exception:
        pass
    return None


# ── CLI main ───────────────────────────────────────────────────────────

def cli_main():
    global _cur_app_name, _cur_lang
    _load_lang()
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
            if not str(target.resolve()).startswith(str(app.presets_dir.resolve())):
                print(_t("cli.invalid_preset", name=sys.argv[2]))
                sys.exit(1)
            # Also try .json for backward compat
            if not target.exists() and ext != ".json":
                target = app.presets_dir / f"{sys.argv[2]}.json"
            if not target.exists():
                print(_t("cli.not_found", name=sys.argv[2]))
                sys.exit(1)
            warn_type, match_name = _analyze_preset_overlap(target)
            if warn_type == "partial":
                print(_t("cli.warning_partial1", name=match_name), file=sys.stderr)
                print(_t("cli.warning_partial2"), file=sys.stderr)
                try:
                    resp = input(_t("cli.proceed")).strip().lower()
                except EOFError:
                    resp = ""
                if resp != "y":
                    print(_t("cli.cancelled"))
                    return
            elif warn_type == "none":
                print(_t("cli.warning_none1"), file=sys.stderr)
                print(_t("cli.warning_none2"), file=sys.stderr)
                try:
                    resp = input(_t("cli.proceed")).strip().lower()
                except EOFError:
                    resp = ""
                if resp != "y":
                    print(_t("cli.cancelled"))
                    return
            activate(target)
            print(_t("cli.activated", name=sys.argv[2]))
            return
        if cmd == "current":
            print(get_active() or _t("cli.unknown"))
            return
        if cmd == "backup":
            if len(sys.argv) < 3:
                print(_t("cli.backup_usage"))
                sys.exit(1)
            name = sys.argv[2]
            try:
                target = backup_live_as_preset(name)
            except ValueError:
                print(_t("cli.invalid_preset", name=name))
                sys.exit(1)
            except FileExistsError:
                print(_t("cli.preset_exists", name=name))
                sys.exit(1)
            except FileNotFoundError:
                print(_t("cli.no_live_config"))
                sys.exit(1)
            except Exception as e:
                print(_t("cli.backup_failed", error=str(e)))
                sys.exit(1)
            print(_t("cli.backed_up_live", name=target.stem))
            return
        if cmd == "diff" and len(sys.argv) >= 3:
            ext = _preset_ext(app)
            target = app.presets_dir / f"{sys.argv[2]}{ext}"
            if not str(target.resolve()).startswith(str(app.presets_dir.resolve())):
                print(_t("cli.invalid_preset", name=sys.argv[2]))
                sys.exit(1)
            if not target.exists() and ext != ".json":
                target = app.presets_dir / f"{sys.argv[2]}.json"
            if not target.exists():
                print(_t("cli.not_found", name=sys.argv[2]))
                sys.exit(1)
            show_diff(target)
            return
        if cmd == "backups":
            backups = list_backups()
            if not backups:
                print(_t("cli.no_backups"))
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
            if not str(target.resolve()).startswith(str(app.backup_dir.resolve())):
                print(_t("cli.invalid_backup", name=name))
                sys.exit(1)
            if not target.exists():
                print(_t("cli.backup_not_found", name=name))
                sys.exit(1)
            restore_backup(target)
            print(_t("cli.restored", name=target.name))
            return
        if cmd == "lang":
            if len(sys.argv) >= 3:
                code = sys.argv[2]
                if code not in ("zh-CN", "zh-TW", "ja", "en"):
                    print(_t("cli.unsupported_lang", code=code))
                    sys.exit(1)
                _cur_lang = code
                try:
                    CLAP_DIR.mkdir(parents=True, exist_ok=True)
                    _atomic_write(LANG_FILE, code)
                except Exception as e:
                    print(_t("msg.lang_save_failed", error=str(e)), file=sys.stderr)
                    sys.exit(1)
                print(_t("cli.lang_set", code=code))
            else:
                labels = {"en": _t("cli.lang_en"), "zh-CN": _t("cli.lang_zhcn"),
                          "zh-TW": _t("cli.lang_zhtw"), "ja": _t("cli.lang_ja")}
                print(_t("cli.current_lang", code=_cur_lang,
                         label=labels.get(_cur_lang, _cur_lang)))
            return
        if cmd in ("-V", "--version", "version"):
            print(_t("cli.version", version=VERSION))
            return
        if cmd in ("-h", "--help", "help"):
            print("Usage:")
            print("  clap                     open TUI")
            print("  clap ls                  list all presets")
            print("  clap use <name>          activate by name")
            print("  clap current             print active preset name")
            print("  clap backup <name>       save current live config as a preset")
            print("  clap diff <name>         diff preset against current settings")
            print("  clap backups             list available backups")
            print("  clap restore <name>      restore a backup (name or timestamp)")
            print("  clap apps                list supported apps")
            print("  clap app <name>          switch default app for CLI commands")
            print("  clap lang [code]         show/set language (zh-CN, zh-TW, ja, en)")
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
                _atomic_write(DEFAULT_APP_FILE, target)
            except Exception:
                pass
            print(f"Switched to {APPS[target].label} ({target})")
            return
        if cmd == "update":
            _cmd_update()
            return

    # Check for updates (once per day, non-blocking)
    update_cache = CLAP_DIR / ".update-check"
    should_check = True
    if update_cache.exists():
        try:
            mtime = update_cache.stat().st_mtime
            if mtime > (datetime.now().timestamp() - 86400):
                should_check = False
        except Exception:
            pass
    if should_check:
        try:
            remote = _check_update()
            if remote and remote != VERSION:
                print(f"\n  Update available: clap v{VERSION} → v{remote}\n"
                      f"  Run: clap update\n", file=sys.stderr)
        except Exception:
            pass
        try:
            CLAP_DIR.mkdir(parents=True, exist_ok=True)
            update_cache.write_text(VERSION)
        except Exception:
            pass

    # Launch TUI
    import curses
    curses.wrapper(lambda s: TUI(s).loop())


if __name__ == "__main__":
    cli_main()
