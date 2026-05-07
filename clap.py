#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 pterchan
"""
Claude+Swap — Switch profiles in a snap (TUI)
Manage multiple Claude Code settings.json profiles from the terminal.
"""
import curses
import difflib
import json
import os
import shutil
import subprocess
import sys
import shlex
from pathlib import Path
from datetime import datetime

VERSION = "0.1.0"

HOME = Path.home()
CLAUDE_DIR = HOME / ".claude"
SETTINGS_FILE = CLAUDE_DIR / "settings.json"
CLAP_DIR = HOME / ".clap"
PRESETS_DIR = CLAP_DIR / "presets"
BACKUP_DIR = CLAP_DIR / "backups"
ACTIVE_FILE = CLAP_DIR / "active"

MIN_H = 12
MIN_W = 70
LABEL_WIDTH = 14
MIN_LIST_W = 28
MAX_BACKUPS = 30

MODE_NEW = "new"
MODE_DUP = "dup"
MODE_RENAME = "rename"

DEFAULT_TEMPLATE = {
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

EXAMPLES = {
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


def _chmod600(path):
    try:
        os.chmod(path, 0o600)
    except Exception as e:
        print(f"Warning: could not chmod 600 {path}: {e}", file=sys.stderr)


def init_dirs():
    CLAP_DIR.mkdir(exist_ok=True)
    PRESETS_DIR.mkdir(exist_ok=True)
    BACKUP_DIR.mkdir(exist_ok=True)
    CLAUDE_DIR.mkdir(exist_ok=True)
    if not list(PRESETS_DIR.glob("*.json")):
        for name, data in EXAMPLES.items():
            p = PRESETS_DIR / f"{name}.json"
            p.write_text(json.dumps(data, indent=2, ensure_ascii=False))
            _chmod600(p)


def list_presets():
    return sorted(PRESETS_DIR.glob("*.json"), key=lambda p: p.stem)


def detect_active_by_content():
    if not SETTINGS_FILE.exists():
        return None
    try:
        current = json.loads(SETTINGS_FILE.read_text())
    except Exception:
        return None
    for p in list_presets():
        try:
            if json.loads(p.read_text()) == current:
                return p.stem
        except Exception:
            pass
    return None


def _prune_backups(max_keep=MAX_BACKUPS):
    try:
        backups = sorted(BACKUP_DIR.glob("settings_*.json"),
                         key=lambda p: p.stat().st_mtime, reverse=True)
        for old in backups[max_keep:]:
            old.unlink()
    except Exception as e:
        print(f"Warning: backup cleanup failed: {e}", file=sys.stderr)


def get_active():
    try:
        if ACTIVE_FILE.exists():
            name = ACTIVE_FILE.read_text().strip()
            if name and (PRESETS_DIR / f"{name}.json").exists():
                return name
    except Exception:
        pass
    return detect_active_by_content()


def list_backups():
    return sorted(BACKUP_DIR.glob("settings_*.json"),
                  key=lambda p: p.stat().st_mtime, reverse=True)


def _backup_current():
    if not SETTINGS_FILE.exists():
        return None
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = BACKUP_DIR / f"settings_{ts}.json"
    try:
        shutil.copy2(SETTINGS_FILE, path)
        _chmod600(path)
        return path
    except Exception:
        return None


def restore_backup(backup_path):
    if not backup_path.exists():
        raise FileNotFoundError(backup_path)
    _backup_current()
    shutil.copy2(backup_path, SETTINGS_FILE)
    _chmod600(SETTINGS_FILE)
    ACTIVE_FILE.write_text("(restored)")
    _chmod600(ACTIVE_FILE)
    _prune_backups()


def activate(preset_path):
    _backup_current()
    shutil.copy2(preset_path, SETTINGS_FILE)
    _chmod600(SETTINGS_FILE)
    ACTIVE_FILE.write_text(preset_path.stem)
    _chmod600(ACTIVE_FILE)
    _prune_backups()


def mask_key(s):
    if not s:
        return "(none)"
    if len(s) <= 12:
        return "***"
    return s[:6] + "***" + s[-4:]


def parse_preset(path):
    try:
        return json.loads(path.read_text()), None
    except Exception as e:
        return None, str(e)


def open_editor(path):
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
    current_text = ""
    if SETTINGS_FILE.exists():
        try:
            current_text = SETTINGS_FILE.read_text()
        except Exception:
            pass
    try:
        preset_text = preset_path.read_text()
    except Exception as e:
        return None, f"Error reading preset: {e}"
    diff = list(difflib.unified_diff(
        current_text.splitlines(keepends=True),
        preset_text.splitlines(keepends=True),
        fromfile=str(SETTINGS_FILE),
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
                curses.doupdate()
            except Exception:
                pass


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
        self.cached_detail = (None, None)
        self.cached_detail_key = None
        self.refresh()

    def refresh(self):
        self.all_presets = list_presets()
        self._apply_filter()
        self.cached_detail_key = None
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
        try:
            curses.start_color()
            curses.use_default_colors()
            curses.init_pair(1, curses.COLOR_CYAN, -1)       # title / info
            curses.init_pair(2, curses.COLOR_GREEN, -1)      # active / success
            curses.init_pair(3, curses.COLOR_YELLOW, -1)     # warn / filter
            curses.init_pair(4, curses.COLOR_RED, -1)        # error / deny
            curses.init_pair(5, curses.COLOR_MAGENTA, -1)    # labels
            curses.init_pair(6, curses.COLOR_WHITE, curses.COLOR_BLUE)   # selected row
            curses.init_pair(7, curses.COLOR_BLACK, curses.COLOR_CYAN)   # key hints
            curses.init_pair(8, curses.COLOR_BLACK, curses.COLOR_GREEN)  # active row bg
        except Exception:
            pass

    def set_message(self, msg, mtype="info"):
        self.message = msg
        self.message_type = mtype

    def safe_addstr(self, y, x, text, attr=0):
        try:
            self.stdscr.addstr(y, x, text, attr)
        except curses.error:
            pass

    def draw(self):
        self.stdscr.erase()
        h, w = self.stdscr.getmaxyx()
        if h < MIN_H or w < MIN_W:
            self.safe_addstr(0, 0, f"Terminal too small (need >= {MIN_W}x{MIN_H})")
            self.stdscr.refresh()
            return

        title = " clap — Claude Code Profile Manager "
        self.safe_addstr(0, 0, title.center(w),
                         curses.color_pair(1) | curses.A_BOLD | curses.A_REVERSE)

        active = self.cached_active
        active_str = active or "(none)"
        self.safe_addstr(1, 0, f"  Active : ", curses.A_DIM)
        self.safe_addstr(1, 10, active_str[:w - 11],
                         curses.color_pair(2) | curses.A_BOLD)
        self.safe_addstr(2, 0, f"  Target : {SETTINGS_FILE}"[:w - 1],
                         curses.A_DIM)

        fb = 1 if self.filter_text else 0
        if fb:
            self.safe_addstr(3, 0, f"  Filter : {self.filter_text}"[:w - 1],
                             curses.color_pair(3))
        list_h = h - 6 - fb
        list_w = max(MIN_LIST_W, w // 3)
        detail_x = list_w + 2
        detail_w = w - detail_x - 1

        self.safe_addstr(4 + fb, 0, "Presets".ljust(list_w),
                         curses.A_UNDERLINE | curses.A_BOLD)
        self.safe_addstr(4 + fb, detail_x, "Details".ljust(detail_w),
                         curses.A_UNDERLINE | curses.A_BOLD)

        if not self.presets:
            self.safe_addstr(6 + fb, 2, "(no presets, press 'n' to create)",
                             curses.A_DIM)
        else:
            visible = list_h - 1
            if self.selected < self.scroll:
                self.scroll = self.selected
            elif self.selected >= self.scroll + visible:
                self.scroll = self.selected - visible + 1

            for i, p in enumerate(self.presets[self.scroll:self.scroll + visible]):
                idx = self.scroll + i
                row = 5 + fb + i
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
            if self.cached_detail_key != sel:
                self.cached_detail = parse_preset(sel)
                self.cached_detail_key = sel
            data, err = self.cached_detail
            self.draw_detail(5 + fb, detail_x, list_h, detail_w, sel, data, err)

        keys = [
            ("↑↓/jk", "Move"), ("Enter", "Activate"), ("e", "Edit"),
            ("n", "New"), ("d", "Dup"), ("R", "Rename"),
            ("D", "Delete"), ("/", "Filter"), ("=", "Diff"),
            ("b", "Backups"), ("r", "Reload"), ("o", "Finder"), ("q", "Quit"),
        ]
        x = 0
        fy = h - 2
        for k, lbl in keys:
            piece = f" {k} "
            if x + len(piece) + len(lbl) + 3 >= w:
                break
            self.safe_addstr(fy, x, piece, curses.color_pair(7) | curses.A_BOLD)
            x += len(piece)
            self.safe_addstr(fy, x, f" {lbl}  ", curses.A_DIM)
            x += len(lbl) + 3

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

    def draw_detail(self, y, x, h, w, path, data, err):
        if err:
            self.safe_addstr(y, x, f"Parse error: {err}"[:w],
                             curses.color_pair(4))
            return

        env = data.get("env", {}) if isinstance(data, dict) else {}
        perms = data.get("permissions", {}) if isinstance(data, dict) else {}

        api_key = env.get("ANTHROPIC_API_KEY") or env.get("ANTHROPIC_AUTH_TOKEN", "")
        base_url = env.get("ANTHROPIC_BASE_URL", "(default)")
        model = env.get("ANTHROPIC_MODEL", "(default)")
        small = env.get("ANTHROPIC_SMALL_FAST_MODEL", "(default)")
        max_tok = env.get("CLAUDE_CODE_MAX_OUTPUT_TOKENS", "(default)")
        auth_kind = "AUTH_TOKEN" if env.get("ANTHROPIC_AUTH_TOKEN") else "API_KEY"

        # rows: (label, value, color_pair_for_value)
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
        self.input_prompt = "New preset name (without .json): "
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
        try:
            if sys.platform == "darwin":
                subprocess.run(["open", str(PRESETS_DIR)])
            else:
                subprocess.run(["xdg-open", str(PRESETS_DIR)])
            self.set_message(f"Opened {PRESETS_DIR}", "info")
        except Exception as e:
            self.set_message(f"Open dir failed: {e}", "error")

    def handle_input(self, key):
        if key in (10, 13):
            name = self.input_buffer.strip()
            if name:
                target = PRESETS_DIR / f"{name}.json"
                if target.exists():
                    self.set_message(f"'{name}' already exists", "error")
                    return
                if self.input_mode == MODE_NEW:
                    target.write_text(
                        json.dumps(DEFAULT_TEMPLATE, indent=2,
                                   ensure_ascii=False))
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

    def loop(self):
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
            elif key == curses.KEY_RESIZE:
                pass


def _cmd_update():
    import urllib.request
    import tempfile
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

    # Extract VERSION from downloaded source
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


def cli_main():
    init_dirs()
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in ("ls", "list"):
            active = get_active()
            for p in list_presets():
                marker = " * " if p.stem == active else "   "
                print(f"{marker}{p.stem}")
            return
        if cmd == "use" and len(sys.argv) >= 3:
            target = PRESETS_DIR / f"{sys.argv[2]}.json"
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
            target = PRESETS_DIR / f"{sys.argv[2]}.json"
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
                target = BACKUP_DIR / name
            else:
                target = BACKUP_DIR / f"settings_{name}.json"
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
            print("  clap                   open TUI")
            print("  clap ls                list all presets")
            print("  clap use <name>        activate by name")
            print("  clap current           print active preset name")
            print("  clap diff <name>       diff preset against current settings")
            print("  clap backups           list available backups")
            print("  clap restore <name>    restore a backup (name or timestamp)")
            print("  clap update            update clap to the latest version")
            print(f"\nPresets dir: {PRESETS_DIR}")
            print(f"Backups dir: {BACKUP_DIR}")
            return
        if cmd == "update":
            _cmd_update()
            return
    curses.wrapper(lambda s: TUI(s).loop())


if __name__ == "__main__":
    cli_main()
