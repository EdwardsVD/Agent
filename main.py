#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent CLI — coding agent Python dengan SUPERPOWERS
===========================================================================
Bukan cuma tools, tapi DISIPLIN KERJA. Agent dipaksa lewat SOP:
skill check -> brainstorm + approval -> rencana -> TDD -> verifikasi ->
self review -> baru boleh bilang DONE.

    git clone https://github.com/EdwardsVD/Agent.git
    cd Agent
    pip install -r requirements.txt
    python3 main.py

v3.1.0 — fix Termux & anti-akal-akalan:
    - run.sh: launcher yang selalu cd ke folder Agent yang bener, jadi error
      "can't open file .../Agent/Agent/main.py" gak mungkin kejadian lagi.
    - --doctor / /doctor: cek instalasi + kasih tau cara benerin kalau rusak.
    - Lebar terminal ngikut layar HP (dulu dipaksa min 50 kolom -> jebol).
    - Gate gak bisa diakalin: `python3 --version` bukan bukti verifikasi, dan
      file test kosong/stub gak lolos gate TDD (harus ada assertion).
    - Skill lengkap 42 file + references/agent-cli-tools.md khusus harness ini.

v3.0.0 (SUPERPOWERS):
    - 14 skill markdown asli dari github.com/obra/superpowers, di-vendor ke
      folder skills/ (jadi jalan di Termux tanpa internet & tanpa npm).
      Dibaca on-demand lewat tool `skill` — progressive disclosure, context aman.
    - 5 WORKFLOW GATE di level kode yang beneran nge-block aksi agent kalau
      dia nyalip alur: using-superpowers, brainstorming HARD-GATE (approval),
      test-driven-development (test dulu!), writing-plans, dan
      verification-before-completion + self review.
    - Tool baru: skill, list_skills, todo_write, ask_user (agent nanya balik
      dan NUNGGU jawaban manusia — ini yang bikin approval gate beneran jalan).
    - Struk kerja tiap DONE: skill dipakai, approval, bukti verifikasi.
    - Perintah: /skills, /skills <nama>, /superpowers on|off|gates|reload
    - Test: python3 -m unittest discover -s tests   (89 test)

Warisan v2.1.0: intro animasi matrix + logo AGENT + loading, thinking yang bisa
dibuka/tutup, AI search DDG/SearXNG, /download zip, '!'<cmd> buat bash langsung.

Koneksi API: template Xkiro.com (OpenAI-compatible). API key lewat /connect
atau env XKIRO_API_KEY. Konfigurasi tersimpan di ~/.opencode_clone/connect.json

Skill di folder skills/ = MIT (c) 2025 Jesse Vincent — lihat skills/NOTICE.md
"""

import os
import re
import sys
import json
import time
import random
import zipfile
import getpass
import shutil
import textwrap
import subprocess
import urllib.parse
from html import unescape as _html_unescape
from html.parser import HTMLParser

import requests

# ============================================================================
# KONSTANTA & KONFIGURASI
# ============================================================================

VERSION = "3.1.0"

CONFIG_DIR = os.path.expanduser("~/.opencode_clone")
CONFIG_PATH = os.path.join(CONFIG_DIR, "connect.json")

WORKSPACE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "workspace")
)

UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

DEFAULT_CONFIG = {
    "provider": "xkiro",
    "base_url": "https://api.xkiro.com/v1",
    "auth_header": "Authorization",       # atau "x-api-key"
    "api_key": "",
    "default_model_key": "sonnet46",
    "default_effort": "medium",
    "thinking": True,                     # reasoning model aktif?
    "show_thinking": True,                # blok thinking ditampilkan?
    "search_engine": "auto",              # auto | ddg | searxng
    "searxng_url": "",                    # instance SearXNG sendiri (opsional)
    "max_steps": 40,                      # maks. langkah agent per tugas
    "stream": True,                       # streaming (fallback otomatis)
    "superpowers": True,                  # metodologi Superpowers (skill + SOP)
    "gates": True,                        # gate keras: approval, TDD, verifikasi
}


def ensure_config_dir():
    os.makedirs(CONFIG_DIR, exist_ok=True)


def load_config():
    ensure_config_dir()
    cfg = dict(DEFAULT_CONFIG)
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                saved = json.load(f)
            if isinstance(saved, dict):
                cfg.update(saved)
        except Exception:
            pass
    env_key = os.environ.get("XKIRO_API_KEY", "")
    if env_key and not cfg.get("api_key"):
        cfg["api_key"] = env_key
    if not cfg.get("searxng_url"):
        cfg["searxng_url"] = os.environ.get("SEARXNG_URL", "")
    return cfg


def save_config(cfg):
    ensure_config_dir()
    to_save = dict(cfg)
    with open(CONFIG_PATH, "w") as f:
        json.dump(to_save, f, indent=2)
    try:
        os.chmod(CONFIG_PATH, 0o600)
    except Exception:
        pass


def build_auth_headers(cfg):
    key = cfg.get("api_key", "")
    if cfg.get("auth_header") == "x-api-key":
        return {"x-api-key": key}
    return {"Authorization": f"Bearer {key}"}


# ============================================================================
# WARNA / UI TERMINAL
# ============================================================================

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

FG_WHITE = "\033[97m"
FG_BLACK = "\033[30m"
FG_GREEN = "\033[92m"
FG_DARKGREEN = "\033[32m"
FG_YELLOW = "\033[93m"
FG_CYAN = "\033[96m"
FG_RED = "\033[91m"
FG_GREY = "\033[37m"
FG_MAGENTA = "\033[95m"

BG_BLUE = "\033[44m"
BG_DARKGREY = "\033[100m"
BG_GREEN = "\033[42m"


def term_width(default=78):
    """Lebar terminal. Di HP/Termux layarnya sempit (sering 30-45 kolom), jadi
    JANGAN dipaksa minimal 50 — nanti panel & wrapping-nya jebol ke samping."""
    try:
        cols = shutil.get_terminal_size().columns
    except Exception:
        return default
    if not cols or cols <= 0:
        return default
    return max(24, min(100, cols))


def is_narrow():
    """HP mode: layar sempit, hemat hiasan biar gak berantakan."""
    return term_width() < 60


def _visible_len(s):
    out = 0
    i = 0
    while i < len(s):
        if s[i] == "\033":
            j = s.find("m", i)
            if j == -1:
                break
            i = j + 1
            continue
        out += 1
        i += 1
    return out


def _wrap_lines(text, width):
    lines = []
    for raw_line in text.splitlines() or [""]:
        wrapped = textwrap.wrap(
            raw_line, width=width, break_long_words=True, break_on_hyphens=False
        ) or [""]
        lines.extend(wrapped)
    return lines


# ---------------------------------------------------------------------------
# INTRO ANIMASI: matrix hijau full screen + logo AGENT + loading 1-100
# ---------------------------------------------------------------------------

MATRIX_CHARS = "0123456789ABCDEF#$%&@*+=/\\<>|"

LOGO = [
    " █████╗  ██████╗ ███████╗███╗   ██╗████████╗",
    "██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝",
    "███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║",
    "██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║",
    "██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║",
    "╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝",
]


def _is_tty():
    try:
        return sys.stdin.isatty() and sys.stdout.isatty()
    except Exception:
        return False


def _anim_enabled():
    if not _is_tty():
        return False
    if "--no-anim" in sys.argv:
        return False
    if os.environ.get("AGENT_INTRO", "").lower() in ("0", "off", "no", "false"):
        return False
    return True


def _matrix_rain(duration=1.8):
    """Hujan angka ijo random full screen (efek hacker/matrix)."""
    try:
        size = shutil.get_terminal_size()
        h, w = size.lines, size.columns
    except Exception:
        return
    if h < 6 or w < 12:
        return
    frames = max(1, int(duration * 18))
    interval = duration / frames
    try:
        for _ in range(frames):
            lines = []
            for _ in range(max(1, h - 1)):
                row = []
                for _ in range(w):
                    if random.random() < 0.34:
                        ch = random.choice(MATRIX_CHARS)
                        if random.random() < 0.25:
                            row.append(FG_GREEN + ch)
                        else:
                            row.append(FG_DARKGREEN + ch)
                    else:
                        row.append(" ")
                lines.append("".join(row))
            sys.stdout.write("\033[H" + "\n".join(lines) + RESET)
            sys.stdout.flush()
            time.sleep(interval)
    except KeyboardInterrupt:
        pass


def _show_logo_and_loading(load_duration=1.8):
    """Logo AGENT + loading 1-100% di tengah layar."""
    try:
        size = shutil.get_terminal_size()
        h, w = size.lines, size.columns
    except Exception:
        h, w = 24, 80

    logo = LOGO if w >= 62 else []
    pad_top = max(0, (h - len(logo) - 7) // 2)
    sys.stdout.write("\n" * pad_top)
    for line in logo:
        sys.stdout.write(f"{FG_GREEN}{BOLD}{line.center(w)}{RESET}\n")
    tag = f"AGENT v{VERSION} · superpower edition · thinking + AI search"
    sys.stdout.write(f"{FG_CYAN}{tag.center(w)}{RESET}\n\n")

    bar_w = max(12, min(48, w - 14))
    steps = 100
    step_delay = load_duration / steps
    try:
        for pct in range(1, steps + 1):
            filled = int(bar_w * pct / steps)
            bar = "█" * filled + "░" * (bar_w - filled)
            sys.stdout.write(
                f"\r{(' ' * max(0, (w - bar_w - 12) // 2))}"
                f"{FG_GREEN}[{bar}]{RESET} {FG_GREEN}{BOLD}{pct:3d}%{RESET}"
            )
            sys.stdout.flush()
            time.sleep(step_delay)
    except KeyboardInterrupt:
        sys.stdout.write(f"\r{FG_GREEN}{'OK — lanjut'.center(w)}{RESET}")
        sys.stdout.flush()
        time.sleep(0.3)
    sys.stdout.write("\n")


def intro_animation(duration=1.8, load_duration=1.8):
    """Animasi pembuka: matrix -> logo -> loading 1-100 -> clear screen.
    Di-skip otomatis kalau bukan terminal interaktif (mis. piped stdin)."""
    if not _anim_enabled():
        return
    hide = "\033[?25l"
    show = "\033[?25h"
    try:
        sys.stdout.write("\033[2J\033[H" + hide)
        sys.stdout.flush()
        _matrix_rain(duration)
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()
        _show_logo_and_loading(load_duration)
        sys.stdout.write("\033[2J\033[H" + show)
        sys.stdout.flush()
    finally:
        sys.stdout.write(show)
        sys.stdout.flush()


def banner():
    w = term_width()
    title = f"Agent CLI v{VERSION}  ·  🦸 Superpowers + thinking + AI search"
    line = "═" * w
    print(f"{FG_CYAN}{BOLD}{line}{RESET}")
    print(f"{FG_CYAN}{BOLD}{title.center(w)}{RESET}")
    print(f"{FG_CYAN}{BOLD}{line}{RESET}")
    n_skills = len(load_skills())
    if n_skills:
        print(
            f"{DIM}Ketik tugas biasa buat agent. Metodologi Superpowers aktif "
            f"({n_skills} skill: brainstorm → approval → plan → TDD → verifikasi).{RESET}"
        )
        print(
            f"{DIM}'/skills' lihat skill, '/superpowers' atur metodologi, "
            f"'/help' daftar perintah, '/intro' animasi lagi.{RESET}\n"
        )
    else:
        print(
            f"{FG_RED}{BOLD}⚠ Folder skills/ gak ketemu — Superpowers MATI, agent "
            f"jalan mode polos.{RESET}"
        )
        print(
            f"{FG_YELLOW}  Clone repo-nya lengkap biar dapet 14 skill:{RESET}\n"
            f"{FG_YELLOW}  git clone https://github.com/EdwardsVD/Agent.git{RESET}\n"
        )


def toolbar(state):
    w = term_width()
    model = state.model
    effort_display = "OFF" if not state.thinking_on else state.effort.upper()
    if state.thinking_on:
        think_display = "ON · TAMPIL" if state.show_thinking else "ON · SEMBUNYI"
    else:
        think_display = "OFF"
    engine = state.config.get("search_engine", "auto")
    if engine == "auto":
        engine = "auto(SearXNG)" if state.config.get("searxng_url") else "auto(DDG)"

    conn = state.config.get("api_key", "")
    if conn:
        masked = conn[:4] + "…" + conn[-4:] if len(conn) > 8 else "*" * len(conn)
        conn_text = f"connected ({masked})"
        conn_color = FG_GREEN
    else:
        conn_text = "belum /connect"
        conn_color = FG_RED

    left = f" Model: {model['label']} "
    mid1 = f" Upaya: {effort_display} "
    mid2 = f" Thinking: {think_display} "
    mid3 = f" Search: {engine} "
    right = f" Langkah: {state.step_count}/{state.max_steps} "

    line1 = f"{BG_DARKGREY}{FG_WHITE}{BOLD}{left}{RESET}"
    line1 += f"{BG_DARKGREY}{FG_YELLOW}{mid1}{RESET}"
    line1 += f"{BG_DARKGREY}{FG_MAGENTA}{mid2}{RESET}"
    line1 += f"{BG_DARKGREY}{FG_CYAN}{mid3}{RESET}"
    line1 += f"{BG_DARKGREY}{FG_WHITE}{right}{RESET}"
    pad = max(0, w - _visible_len(line1))
    line1 += f"{BG_DARKGREY}{' ' * pad}{RESET}"

    n_skills = len(load_skills())
    sp_on = bool(state.config.get("superpowers", True)) and n_skills > 0
    gates_on = sp_on and state.config.get("gates", True)
    if not n_skills:
        sp_text = " 🦸 Superpowers: OFF (skills/ gak ada) "
        sp_color = FG_RED
    else:
        sp_text = f" 🦸 Superpowers: {'ON' if sp_on else 'OFF'}"
        sp_text += f" (gates {'ON' if gates_on else 'OFF'}) " if sp_on else " "
        sp_color = FG_GREEN if sp_on else FG_GREY

    line2_text = f" Status: {conn_text} "
    line2 = f"{BG_DARKGREY}{conn_color}{BOLD}{line2_text}{RESET}"
    line2 += f"{BG_DARKGREY}{sp_color}{BOLD}{sp_text}{RESET}"
    line2 += f"{BG_DARKGREY}{DIM} Endpoint: {state.config.get('base_url', '-')} {RESET}"
    pad2 = max(0, w - _visible_len(line2))
    line2 += f"{BG_DARKGREY}{' ' * pad2}{RESET}"

    print(line1)
    print(line2)


def user_bubble(text):
    w = term_width()
    inner_w = w - 4
    print()
    print(f"{BG_BLUE}{FG_WHITE}{BOLD}{' You'.ljust(w)}{RESET}")
    for line in _wrap_lines(text, inner_w):
        content = f"  {line}"
        pad = " " * max(0, w - len(content))
        print(f"{BG_BLUE}{FG_WHITE}{content}{pad}{RESET}")
    print()


def thinking_header(label="🧠 Thinking"):
    w = term_width()
    bar = "─" * max(0, w - _visible_len(label) - 1)
    print(f"{FG_MAGENTA}{BOLD}{label}{RESET}{FG_MAGENTA} {bar}{RESET}", flush=True)


def thinking_chunk(text):
    for line in text.splitlines():
        print(f"{FG_MAGENTA}{DIM} {line}{RESET}", flush=True)


def thinking_footer():
    w = term_width()
    print(f"{FG_MAGENTA}{'─' * w}{RESET}")


def thinking_block(text, label="🧠 Thinking"):
    w = term_width()
    bar = "─" * max(0, w - _visible_len(label) - 1)
    print(f"{FG_MAGENTA}{BOLD}{label}{RESET}{FG_MAGENTA} {bar}{RESET}")
    for line in _wrap_lines(text, w - 2):
        print(f"{FG_MAGENTA}{DIM} {line}{RESET}")
    print(f"{FG_MAGENTA}{'─' * w}{RESET}")


def _action_label(tool_name, args):
    a = args or {}
    styles = {
        "list_files": ("📂 List", str(a.get("path", "."))),
        "grep_files": ("🔍 Grep", '"{}" di {}'.format(a.get("pattern", "?"), a.get("path", "."))),
        "read_file": ("📖 Baca", str(a.get("path", "?"))),
        "write_file": ("📝 Tulis", str(a.get("path", "?"))),
        "edit_file": ("✏️ Edit", str(a.get("path", "?"))),
        "bash": ("💻 Bash", str(a.get("command", "?"))),
        "web_search": (
            "🔎 Search",
            '"{q}" (limit={l}, engine={e})'.format(
                q=a.get("query", "?"), l=a.get("limit", 5), e=a.get("engine", "auto")
            ),
        ),
        "web_fetch": ("📄 Fetch", str(a.get("url", "?"))),
        "skill": (
            "🦸 Skill",
            "{}{}".format(
                a.get("name") or a.get("skill") or "?",
                f" / {a.get('resource')}" if a.get("resource") else "",
            ),
        ),
        "list_skills": ("🦸 Skills", "daftar semua skill Superpowers"),
        "todo_write": ("📋 Rencana", f"{len(a.get('todos') or [])} task"),
        "ask_user": ("🙋 Tanya", str(a.get("question", "?"))[:100]),
    }
    return styles.get(tool_name, (f"⚙ {tool_name}", json.dumps(a, ensure_ascii=False)[:120]))


def action_line(tool_name, args):
    icon, detail = _action_label(tool_name, args)
    print(f"{FG_YELLOW}{BOLD}{icon}{RESET} {FG_YELLOW}{detail}{RESET}")


def observation_line(text, tool_name=None):
    w = term_width()
    lines = _wrap_lines(text, w)
    if tool_name in ("web_search", "web_fetch") and lines:
        print(f"{DIM}{FG_GREY}  ↳ {lines[0]}{RESET}")
        for line in lines[1:]:
            print(f"{DIM}{FG_GREY}    {line}{RESET}")
    else:
        for line in lines:
            print(f"{DIM}{FG_GREY}  ↳ {line}{RESET}")
    print()


def system_line(text, color=FG_CYAN):
    print(f"{color}{text}{RESET}")


def error_line(text):
    print(f"{FG_RED}{BOLD}✖ {text}{RESET}")


def success_line(text):
    print(f"{FG_GREEN}{BOLD}✔ {text}{RESET}")


def done_line(summary):
    w = term_width()
    print(f"{BG_GREEN}{FG_BLACK}{BOLD}{' DONE '.ljust(w)}{RESET}")
    for line in _wrap_lines(summary, w):
        print(f"{FG_GREEN}{line}{RESET}")
    print()


# --- tampilan khusus Superpowers -------------------------------------------

def skill_line(key, purpose=""):
    tail = f" {DIM}→ {purpose}{RESET}" if purpose else ""
    print(f"{FG_CYAN}{BOLD}🦸 Using skill{RESET} {FG_CYAN}{key}{RESET}{tail}")


def gate_line(text):
    """Blok merah waktu disiplin Superpowers nge-block aksi agent."""
    w = term_width()
    lines = text.splitlines() or [""]
    head = lines[0]
    print(f"{FG_RED}{BOLD}🛑 {head}{RESET}")
    for line in lines[1:]:
        for wrapped in _wrap_lines(line, w - 3):
            print(f"{FG_RED}{DIM}   {wrapped}{RESET}")
    print()


TODO_MARK = {
    "done": ("✔", FG_GREEN),
    "in_progress": ("▶", FG_YELLOW),
    "blocked": ("✖", FG_RED),
    "pending": ("○", FG_GREY),
}


def todo_panel(todos):
    w = term_width()
    done = sum(1 for t in todos if t.get("status") == "done")
    title = f" 📋 Rencana kerja  ({done}/{len(todos)} beres) "
    print(f"{BG_DARKGREY}{FG_WHITE}{BOLD}{title.ljust(w)}{RESET}")
    for t in todos:
        mark, color = TODO_MARK.get(t.get("status", "pending"), TODO_MARK["pending"])
        style = DIM if t.get("status") == "done" else ""
        print(f"  {color}{BOLD}{mark}{RESET} {style}{t.get('task', '')}{RESET}")
    print()


def question_panel(question, options):
    w = term_width()
    print()
    print(f"{BG_BLUE}{FG_WHITE}{BOLD}{' 🙋 Butuh keputusan kamu '.ljust(w)}{RESET}")
    for line in _wrap_lines(question, w - 2):
        print(f"{FG_WHITE}{BOLD} {line}{RESET}")
    for i, opt in enumerate(options, 1):
        print(f"   {FG_CYAN}{BOLD}{i}.{RESET} {FG_CYAN}{opt}{RESET}")
    if options:
        print(f"{DIM}   (ketik nomor / jawaban bebas, Enter = pilihan 1){RESET}")
    else:
        print(f"{DIM}   (ketik jawaban kamu, Enter = setuju){RESET}")


# ============================================================================
# KATALOG MODEL + LEVEL UPAYA (Xkiro.com)
# ============================================================================

EFFORT_ALIASES = {
    "none": "none", "off": "none", "nol": "none",
    "low": "low", "rendah": "low",
    "med": "medium", "medium": "medium", "sedang": "medium",
    "high": "high", "tinggi": "high",
    "xhigh": "xhigh", "extreme": "xhigh", "extrem": "xhigh", "ekstrem": "xhigh",
    "max": "max", "maks": "max", "maksimal": "max",
}

EFFORT_ORDER = ["none", "low", "medium", "high", "xhigh", "max"]

MODEL_CATALOG = [
    {"key": "fable5", "label": "Claude Fable 5", "id": "anthropic/claude-fable-5",
     "vendor": "Anthropic", "efforts": ["low", "medium", "high", "xhigh", "max"], "default_effort": "high"},
    {"key": "opus5", "label": "Claude Opus 5", "id": "anthropic/claude-opus-5",
     "vendor": "Anthropic", "efforts": ["low", "medium", "high", "xhigh", "max"], "default_effort": "high"},
    {"key": "sonnet5", "label": "Claude Sonnet 5", "id": "anthropic/claude-sonnet-5",
     "vendor": "Anthropic", "efforts": ["low", "medium", "high", "xhigh", "max"], "default_effort": "medium"},
    {"key": "sonnet46", "label": "Claude Sonnet 4.6", "id": "anthropic/claude-sonnet-4.6",
     "vendor": "Anthropic", "efforts": ["low", "medium", "high", "max"], "default_effort": "medium"},
    {"key": "opus46", "label": "Claude Opus 4.6", "id": "anthropic/claude-opus-4.6",
     "vendor": "Anthropic", "efforts": ["low", "medium", "high", "max"], "default_effort": "high"},
    {"key": "gpt56sol", "label": "GPT-5.6 Sol", "id": "openai/gpt-5.6-sol",
     "vendor": "OpenAI", "efforts": ["none", "low", "medium", "high", "xhigh", "max"], "default_effort": "high"},
    {"key": "gpt56terra", "label": "GPT-5.6 Terra", "id": "openai/gpt-5.6-terra",
     "vendor": "OpenAI", "efforts": ["none", "low", "medium", "high", "xhigh", "max"], "default_effort": "high"},
    {"key": "gpt56luna", "label": "GPT-5.6 Luna", "id": "openai/gpt-5.6-luna",
     "vendor": "OpenAI", "efforts": ["none", "low", "medium", "high", "xhigh", "max"], "default_effort": "high"},
    {"key": "qwen38max", "label": "Qwen3.8 Max", "id": "qwen/qwen3.8-max",
     "vendor": "Alibaba", "efforts": ["low", "medium", "xhigh"], "default_effort": "xhigh"},
    {"key": "kimik3", "label": "Kimi K3", "id": "moonshot/kimi-k3",
     "vendor": "Moonshot AI", "efforts": ["low", "high", "max"], "default_effort": "max"},
]

DEFAULT_MODEL_KEY = "sonnet46"


def find_model(query):
    query = query.strip()
    if not query:
        return None
    if query.isdigit():
        idx = int(query) - 1
        if 0 <= idx < len(MODEL_CATALOG):
            return MODEL_CATALOG[idx]
        return None
    q = query.lower()
    for m in MODEL_CATALOG:
        if q == m["key"].lower() or q == m["id"].lower():
            return m
    for m in MODEL_CATALOG:
        if q in m["key"].lower() or q in m["label"].lower() or q in m["id"].lower():
            return m
    return None


def get_model_by_key(key):
    for m in MODEL_CATALOG:
        if m["key"] == key:
            return m
    return MODEL_CATALOG[0]


def normalize_effort(raw):
    if not raw:
        return None
    return EFFORT_ALIASES.get(raw.strip().lower())


def closest_supported_effort(model, effort):
    supported = model["efforts"]
    if effort in supported:
        return effort
    if effort not in EFFORT_ORDER:
        return model["default_effort"]
    target_idx = EFFORT_ORDER.index(effort)
    best, best_dist = None, None
    for lvl in supported:
        dist = abs(EFFORT_ORDER.index(lvl) - target_idx)
        if best_dist is None or dist < best_dist:
            best, best_dist = lvl, dist
    return best or model["default_effort"]


# ============================================================================
# KLIEN API (OpenAI-compatible, streaming + fallback non-stream)
# ============================================================================

class ApiError(Exception):
    pass


class StreamError(Exception):
    pass


def extract_reasoning_text(obj):
    """Ambil teks reasoning model dari berbagai bentuk field (reasoning_content,
    reasoning, thinking) — dipakai buat blok thinking yang ditampilkan."""
    if not isinstance(obj, dict):
        return ""
    for key in ("reasoning_content", "reasoning", "thinking"):
        v = obj.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()
        if isinstance(v, dict):
            t = v.get("text") or v.get("content") or v.get("summary")
            if t:
                return str(t).strip()
    return ""


def _chat_streamed(url, headers, payload, timeout, on_stream):
    payload = dict(payload)
    payload["stream"] = True
    content_parts = []
    thinking_parts = []
    saw_data = False

    with requests.post(url, headers=headers, json=payload,
                       stream=True, timeout=(15, timeout)) as resp:
        if resp.status_code != 200:
            try:
                body = "".join(
                    chunk.decode("utf-8", errors="replace")
                    for chunk in resp.iter_content(4096)
                )[:500]
            except Exception:
                body = ""
            raise StreamError(f"HTTP {resp.status_code}: {body}")

        for raw in resp.iter_lines(decode_unicode=True):
            if not raw:
                continue
            raw = raw.strip()
            if not raw.startswith("data:"):
                continue
            saw_data = True
            chunk = raw[5:].strip()
            if chunk == "[DONE]":
                break
            try:
                obj = json.loads(chunk)
            except ValueError:
                continue
            choices = obj.get("choices") or []
            delta = choices[0].get("delta", {}) if choices else {}
            msg = choices[0].get("message", {}) if choices else {}
            think = extract_reasoning_text(delta) or extract_reasoning_text(msg)
            cont = delta.get("content") or msg.get("content") or ""
            if think:
                thinking_parts.append(think)
                if on_stream:
                    on_stream("thinking", think)
            if cont:
                content_parts.append(cont)
                if on_stream:
                    on_stream("content", cont)

    content = "".join(content_parts)
    thinking = "".join(thinking_parts)
    if not saw_data or not content:
        raise StreamError("Respons stream kosong / tanpa konten")
    return {"content": content, "thinking": thinking}


def _chat_plain(url, headers, payload, timeout):
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    except requests.RequestException as e:
        raise ApiError(f"Gagal konek ke {url}: {e}")
    if resp.status_code != 200:
        raise ApiError(f"HTTP {resp.status_code} dari provider: {resp.text[:500]}")
    try:
        data = resp.json()
        msg = data["choices"][0].get("message", {})
        content = msg.get("content") or ""
        thinking = extract_reasoning_text(msg)
        if not content:
            raise ApiError("Respons tidak berisi konten.")
        return {"content": content, "thinking": thinking}
    except ApiError:
        raise
    except Exception as e:
        raise ApiError(f"Format respons tidak dikenali: {e} — raw: {resp.text[:500]}")


def send_chat(cfg, model_id, messages, effort, thinking_on,
              max_tokens=4096, timeout=120, on_stream=None):
    if not cfg.get("api_key"):
        raise ApiError("Belum ada API key. Jalankan '/connect' dulu (atau set XKIRO_API_KEY).")

    base_url = (cfg.get("base_url") or DEFAULT_CONFIG["base_url"]).rstrip("/")
    url = f"{base_url}/chat/completions"
    headers = {"Content-Type": "application/json"}
    headers.update(build_auth_headers(cfg))

    payload = {
        "model": model_id,
        "messages": messages,
        "max_tokens": max_tokens,
    }
    if not thinking_on:
        payload["reasoning"] = {"enabled": False}
    else:
        payload["reasoning"] = {"effort": effort}

    if cfg.get("stream", True):
        try:
            return _chat_streamed(url, headers, payload, timeout, on_stream)
        except StreamError:
            pass  # fallback ke non-stream
    return _chat_plain(url, headers, payload, timeout)


def test_connection(cfg, timeout=15):
    """/connect test — cek base_url + api key valid."""
    if not cfg.get("api_key"):
        return False, "API key kosong."
    base_url = (cfg.get("base_url") or DEFAULT_CONFIG["base_url"]).rstrip("/")
    headers = build_auth_headers(cfg)
    try:
        resp = requests.get(f"{base_url}/models", headers=headers, timeout=timeout)
    except requests.RequestException as e:
        return False, f"Gagal konek: {e}"
    if resp.status_code == 200:
        return True, "Koneksi OK (GET /models berhasil)."
    if resp.status_code in (401, 403):
        return False, f"Auth ditolak (HTTP {resp.status_code}). Cek API key."
    # Banyak gateway OpenAI-compatible gak punya GET /models — coba panggil chat kecil
    model_id = cfg.get("default_model_key", DEFAULT_MODEL_KEY)
    for m in MODEL_CATALOG:
        if m["key"] == model_id:
            model_id = m["id"]
            break
    try:
        resp = requests.post(
            f"{base_url}/chat/completions",
            headers={**headers, "Content-Type": "application/json"},
            json={"model": model_id, "messages": [{"role": "user", "content": "ping"}], "max_tokens": 1},
            timeout=timeout,
        )
    except requests.RequestException as e:
        return False, f"Gagal konek: {e}"
    if resp.status_code in (401, 403):
        return False, f"Auth ditolak (HTTP {resp.status_code}). Cek API key."
    if resp.status_code == 200 or resp.headers.get("content-type", "").startswith("application/json"):
        return True, "Endpoint bisa dihubungi & auth diterima (GET /models gak tersedia)."
    return False, f"HTTP {resp.status_code}: {resp.text[:300]}"


# ============================================================================
# WEB SEARCH: DuckDuckGo (tanpa key) + SearXNG (instance sendiri)
# ============================================================================

_RATE = {"ddg": 0.0, "searxng": 0.0, "fetch": 0.0}


def _throttle(key, gap=1.1):
    wait = _RATE.get(key, 0.0) + gap - time.time()
    if wait > 0:
        time.sleep(wait)
    _RATE[key] = time.time()


def _strip_tags(s):
    return _html_unescape(re.sub(r"<[^>]+>", "", s or ""))


def _clean_ddg_url(href):
    href = (href or "").strip()
    if not href:
        return ""
    if href.startswith("//"):
        href = "https:" + href
    parsed = urllib.parse.urlparse(href)
    if "duckduckgo.com" in (parsed.netloc or ""):
        qs = urllib.parse.parse_qs(parsed.query)
        uddg = qs.get("uddg", [""])[0]
        return uddg
    return href


def _ddg_parse(html_text, limit):
    results = []
    for m in re.finditer(r"<a\b([^>]*)>(.*?)</a>", html_text, re.DOTALL):
        attrs, inner = m.group(1), m.group(2)
        if "result__a" not in attrs:
            continue
        href = re.search(r'href="([^"]+)"', attrs)
        if not href:
            continue
        url = _clean_ddg_url(href.group(1))
        title = _strip_tags(inner).strip()
        if not url or not title:
            continue
        results.append({"title": title, "url": url, "snippet": ""})
        if len(results) >= limit:
            break

    snips = []
    for m in re.finditer(r"<a\b([^>]*)>(.*?)</a>", html_text, re.DOTALL):
        if "result__snippet" in m.group(1):
            snips.append(_strip_tags(m.group(2)).strip())
    for i, r in enumerate(results):
        if i < len(snips):
            r["snippet"] = snips[i]
    return results


def _ddg_search(query, limit):
    hosts = ["https://duckduckgo.com/html/", "https://html.duckduckgo.com/html/"]
    last_err = None
    for _attempt in range(2):
        for host in hosts:
            _throttle("ddg")
            try:
                resp = requests.get(
                    host,
                    params={"q": query},
                    headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"},
                    timeout=15,
                )
            except requests.RequestException as e:
                last_err = e
                continue
            if resp.status_code in (403, 429):
                last_err = RuntimeError(f"HTTP {resp.status_code} (rate-limited)")
                time.sleep(1.5)
                continue
            if resp.status_code != 200:
                last_err = RuntimeError(f"HTTP {resp.status_code}")
                continue
            return _ddg_parse(resp.text, limit)
        time.sleep(1.0)
    if last_err is not None:
        raise RuntimeError(str(last_err))
    return []


def _searxng_html_parse(html_text, limit):
    results = []
    for art in re.findall(r"<article\b.*?</article>", html_text, re.DOTALL):
        m = re.search(
            r"<h3[^>]*>.*?<a\b[^>]*href=\"([^\"]+)\"[^>]*>(.*?)</a>", art, re.DOTALL
        )
        if not m:
            continue
        title = _strip_tags(m.group(2)).strip()
        snip = ""
        sm = re.search(r'<p class="[^"]*content[^"]*"[^>]*>(.*?)</p>', art, re.DOTALL)
        if sm:
            snip = _strip_tags(sm.group(1)).strip()
        results.append({"title": title, "url": m.group(1), "snippet": snip})
        if len(results) >= limit:
            break
    return results


def _searxng_search(base, query, limit):
    base = base.rstrip("/")
    # 1) coba API JSON (butuh instance dengan format=json aktif)
    _throttle("searxng")
    try:
        resp = requests.get(
            f"{base}/search",
            params={"q": query, "format": "json"},
            headers={"User-Agent": UA},
            timeout=15,
        )
        if resp.status_code == 200:
            try:
                data = resp.json()
                results = []
                for it in (data.get("results") or [])[:limit]:
                    results.append({
                        "title": (it.get("title") or "").strip(),
                        "url": it.get("url") or "",
                        "snippet": (it.get("content") or "").strip(),
                    })
                if results:
                    return results
            except ValueError:
                pass
    except requests.RequestException:
        pass
    # 2) fallback: parse halaman HTML SearXNG
    _throttle("searxng")
    try:
        resp = requests.get(
            f"{base}/search", params={"q": query}, headers={"User-Agent": UA}, timeout=15
        )
    except requests.RequestException as e:
        raise RuntimeError(f"gagal konek ({e.__class__.__name__})")
    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code}")
    results = _searxng_html_parse(resp.text, limit)
    if not results:
        raise RuntimeError("tidak ada hasil terparse")
    return results


def _resolve_engine(cfg, engine):
    e = (engine or cfg.get("search_engine") or "auto").strip().lower()
    if e == "auto":
        e = "searxng" if cfg.get("searxng_url") else "ddg"
    if e not in ("ddg", "searxng"):
        e = "ddg"
    return e


def _short_err(e, n=160):
    s = str(e)
    return s if len(s) <= n else s[: n - 1] + "…"


def web_search(cfg, query, limit=5, engine=None):
    """Cari di web. Return (results, engine_dipakai, note)."""
    limit = max(1, min(20, int(limit)))
    engine = _resolve_engine(cfg, engine)
    errors = []

    if engine == "searxng":
        url = (cfg.get("searxng_url") or "").strip()
        if not url:
            engine = "ddg"
            errors.append("SearXNG belum di-set, pakai DDG")
        else:
            try:
                return _searxng_search(url, query, limit), "searxng", ""
            except Exception as e:
                errors.append(f"SearXNG gagal ({_short_err(e)}) — fallback ke DDG")
                engine = "ddg"
    try:
        results = _ddg_search(query, limit)
    except Exception as e:
        errors.append(f"DDG gagal ({_short_err(e)})")
        if errors:
            raise RuntimeError("; ".join(errors))
        raise
    return results, "ddg", "; ".join(errors)


class _TextExtractor(HTMLParser):
    """Ambil judul + teks bersih dari HTML (script/style/noscript dilewati)."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.in_title = False
        self.skip = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self.skip += 1
        elif tag == "title":
            self.in_title = True
        elif tag in ("p", "br", "div", "li", "h1", "h2", "h3", "h4",
                     "tr", "section", "article", "blockquote"):
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript") and self.skip:
            self.skip -= 1
        elif tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.skip:
            return
        if self.in_title:
            self.title += data
        else:
            self.parts.append(data)


def _html_to_text(html_text):
    parser = _TextExtractor()
    try:
        parser.feed(html_text)
    except Exception:
        pass
    body = "".join(parser.parts)
    body = re.sub(r"[ \t]+", " ", body)
    body = re.sub(r"\n{3,}", "\n\n", body)
    return parser.title.strip(), body


def web_fetch(cfg, url, max_chars=6000):
    """Ambil & ekstrak teks sebuah halaman web. Return (judul, teks)."""
    if not re.match(r"^https?://", url or ""):
        raise RuntimeError("URL harus diawali http:// atau https://")
    _throttle("fetch", gap=0.6)
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,text/plain,*/*"},
            timeout=(10, 25),
            allow_redirects=True,
        )
    except requests.RequestException as e:
        raise RuntimeError(f"gagal ambil halaman: {e}")
    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code}")

    raw = resp.content[:3_000_000]
    try:
        text = raw.decode(resp.encoding or "utf-8", errors="replace")
    except Exception:
        text = raw.decode("utf-8", errors="replace")

    head = text[:2000].lower()
    is_html = (
        "html" in (resp.headers.get("content-type", "") or "").lower()
        or "<html" in head
        or "<!doctype" in text[:512].lower()
        or "<body" in head
    )

    if is_html:
        title, body = _html_to_text(text)
    else:
        title, body = "", text

    body = body.strip()
    total = len(body)
    if total > max_chars:
        body = body[:max_chars] + f"\n… [terpotong — total {total} karakter]"
    return title or "(tanpa judul)", body


# ============================================================================
# TOOL SANDBOX (workspace lokal) + TOOL WEB
# ============================================================================

os.makedirs(WORKSPACE_DIR, exist_ok=True)

# file yang dibuat/diubah agent selama TUGAS TERAKHIR (buat fitur /download)
LAST_TASK_FILES = []


def _safe_path(path):
    full = os.path.abspath(os.path.join(WORKSPACE_DIR, path))
    if not full.startswith(WORKSPACE_DIR):
        raise ValueError("Akses di luar workspace ditolak")
    return full


def _record_file(path):
    rel = os.path.relpath(os.path.abspath(path), WORKSPACE_DIR)
    rel = rel.replace(os.sep, "/")
    if rel not in LAST_TASK_FILES:
        LAST_TASK_FILES.append(rel)


def tool_list_files(args, cfg):
    try:
        base = _safe_path(args.get("path", "."))
        max_depth = max(1, min(6, int(args.get("depth", 3))))
        if os.path.isfile(base):
            return f"[OK] {os.path.relpath(base, WORKSPACE_DIR)} (file)"
        lines = []
        count = 0
        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in sorted(dirs) if d not in ("__pycache__", ".git", "node_modules", ".venv")]
            rel_root = os.path.relpath(root, base)
            depth = 0 if rel_root == "." else rel_root.count(os.sep) + 1
            if depth > max_depth:
                dirs[:] = []
                continue
            prefix = "  " * depth
            dir_name = os.path.basename(root) if depth else os.path.basename(base) or "workspace"
            lines.append(f"{prefix}{dir_name}/")
            for f in sorted(files)[:200]:
                try:
                    size = os.path.getsize(os.path.join(root, f))
                except OSError:
                    size = 0
                lines.append(f"{prefix}  {f}  ({size} B)")
                count += 1
            if len(lines) > 400:
                lines.append("… [terpotong, banyak file]")
                break
        return "[OK] Isi folder:\n" + "\n".join(lines) or "[OK] Folder kosong"
    except Exception as e:
        return f"[Error list_files: {e}]"


def tool_grep_files(args, cfg):
    try:
        base = _safe_path(args.get("path", "."))
        pattern = str(args.get("pattern", ""))
        if not pattern:
            return "[Error grep_files: 'pattern' wajib diisi]"
        use_regex = bool(args.get("regex", False))
        limit = max(1, min(100, int(args.get("limit", 50))))
        try:
            needle = re.compile(pattern) if use_regex else None
        except re.error as e:
            return f"[Error grep_files: regex tidak valid ({e})]"
        matches = []
        walked = 0
        targets = [base]
        if os.path.isfile(base):
            targets = [base]
        else:
            for root, dirs, files in os.walk(base):
                dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git", "node_modules", ".venv")]
                targets.extend(os.path.join(root, f) for f in files)
                walked += len(files)
                if walked > 2000:
                    break
        for path in targets:
            rel = os.path.relpath(path, WORKSPACE_DIR).replace(os.sep, "/")
            try:
                if os.path.getsize(path) > 500_000:
                    continue
                with open(path, "r", errors="replace") as f:
                    for lineno, line in enumerate(f, 1):
                        hit = (needle.search(line) if needle else (pattern in line))
                        if hit:
                            matches.append(f"{rel}:{lineno}: {line.rstrip()[:160]}")
                            if len(matches) >= limit:
                                break
            except (OSError, UnicodeDecodeError):
                continue
            if len(matches) >= limit:
                break
        if not matches:
            return f"[OK] '{pattern}' tidak ditemukan di {os.path.relpath(base, WORKSPACE_DIR)}"
        return f"[OK] {len(matches)} cocok untuk '{pattern}':\n" + "\n".join(matches)
    except Exception as e:
        return f"[Error grep_files: {e}]"


def tool_read_file(args, cfg):
    try:
        path = _safe_path(args["path"])
        with open(path, "r") as f:
            content = f.read()
        offset = max(0, int(args.get("offset", 0)))
        limit = int(args.get("limit", 0)) or None
        lines = content.splitlines()
        if offset or limit:
            end = offset + limit if limit else None
            sliced = lines[offset:end]
            head = f"[OK] {args['path']} (baris {offset + 1}-{offset + len(sliced)} dari {len(lines)})\n"
            return head + "\n".join(sliced)
        if len(content) > 60000:
            content = content[:60000] + f"\n… [terpotong — total {len(content)} karakter]"
        return content
    except Exception as e:
        return f"[Error read_file: {e}]"


def tool_write_file(args, cfg):
    try:
        path = _safe_path(args["path"])
        os.makedirs(os.path.dirname(path) or WORKSPACE_DIR, exist_ok=True)
        with open(path, "w") as f:
            f.write(args["content"])
        _record_file(path)
        return f"[OK] File ditulis: {args['path']}"
    except Exception as e:
        return f"[Error write_file: {e}]"


def _fuzzy_replace(content, old, new):
    """Ganti `old` -> `new`. Exact dulu; kalau gagal, coba pencocokan fuzzy
    yang toleran soal whitespace/indentasi (supaya model gak gampang gagal edit)."""
    if old in content:
        if content.count(old) > 1:
            raise ValueError("teks 'old' muncul lebih dari sekali, perjelas")
        return content.replace(old, new)

    old_lines = [l.rstrip() for l in old.splitlines()]
    if not old_lines:
        raise ValueError("teks 'old' kosong")
    pattern_parts = []
    for i, line in enumerate(old_lines):
        if line.strip() == "":
            pattern_parts.append(r"\s*\n")
        else:
            esc = re.escape(line.strip())
            pattern_parts.append(r"[ \t]*" + esc + r"[ \t]*")
            if i < len(old_lines) - 1:
                pattern_parts.append(r"\n")
    pattern = "".join(pattern_parts)
    matches = list(re.finditer(pattern, content))
    if not matches:
        raise ValueError("teks 'old' tidak ditemukan di file")
    if len(matches) > 1:
        raise ValueError("teks 'old' cocok di lebih dari satu tempat, perjelas")
    m = matches[0]
    return content[: m.start()] + new + content[m.end():]


def tool_edit_file(args, cfg):
    try:
        path = _safe_path(args["path"])
        with open(path, "r") as f:
            content = f.read()
        content = _fuzzy_replace(content, args["old"], args["new"])
        with open(path, "w") as f:
            f.write(content)
        _record_file(path)
        return f"[OK] File diedit: {args['path']}"
    except Exception as e:
        return f"[Error edit_file: {e}]"


def tool_bash(args, cfg):
    try:
        timeout = max(1, min(600, int(args.get("timeout", 120))))
        result = subprocess.run(
            args["command"],
            shell=True,
            cwd=WORKSPACE_DIR,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        out = (result.stdout + result.stderr).strip()
        if result.returncode != 0:
            out = (out or "[Tidak ada output]") + f"\n[exit code: {result.returncode}]"
        return out or "[OK] exit code: 0 (tanpa output)"
    except subprocess.TimeoutExpired:
        return "[Error bash: command timeout]"
    except Exception as e:
        return f"[Error bash: {e}]"


def tool_web_search(args, cfg):
    query = str(args.get("query", "")).strip()
    if not query:
        return "[Error web_search: 'query' wajib diisi]"
    limit = max(1, min(20, int(args.get("limit", 5))))
    engine = str(args.get("engine") or "").strip() or None
    try:
        results, used, note = web_search(cfg, query, limit, engine)
    except Exception as e:
        return f"[Error web_search: {e}]"
    header = f"{len(results)} hasil untuk \"{query}\" via {used.upper()}"
    if note:
        header += f"  [{note}]"
    if not results:
        return header
    lines = [header, ""]
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {r['title']}")
        lines.append(f"   {r['url']}")
        snip = (r.get("snippet") or "").strip()
        if snip:
            lines.append(f"   {snip[:200]}")
    return "\n".join(lines)


def tool_web_fetch(args, cfg):
    url = str(args.get("url", "")).strip()
    if not url:
        return "[Error web_fetch: 'url' wajib diisi]"
    try:
        title, text = web_fetch(cfg, url)
        return f"[OK] {title} — {url}\n{text}"
    except Exception as e:
        return f"[Error web_fetch: {e}]"


# ============================================================================
# SUPERPOWERS — skill library (obra/superpowers) + disiplin kerja (workflow gates)
# ============================================================================
# Ini INTI "Superpowers": bukan cuma tools, tapi SOP kerja yang dipaksain ke
# agent — brainstorm dulu -> minta approval -> plan/todo -> TDD (test dulu) ->
# verifikasi bukti -> baru boleh bilang selesai.
#
# Skill markdown ada di folder skills/ (di-vendor dari github.com/obra/superpowers,
# MIT © Jesse Vincent). Agent baca skill on-demand lewat tool `skill` — persis
# pola progressive disclosure-nya Claude Code, jadi context gak jebol.

SKILLS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skills")

# alias biar model gampang manggil skill walau namanya beda dikit
SKILL_ALIASES = {
    "brainstorm": "brainstorming",
    "design": "brainstorming",
    "spec": "brainstorming",
    "tdd": "test-driven-development",
    "test": "test-driven-development",
    "testing": "test-driven-development",
    "plan": "writing-plans",
    "planning": "writing-plans",
    "write-plan": "writing-plans",
    "execute": "executing-plans",
    "debug": "systematic-debugging",
    "debugging": "systematic-debugging",
    "bug": "systematic-debugging",
    "verify": "verification-before-completion",
    "verification": "verification-before-completion",
    "review": "requesting-code-review",
    "code-review": "requesting-code-review",
    "finish": "finishing-a-development-branch",
    "worktree": "using-git-worktrees",
    "worktrees": "using-git-worktrees",
    "subagent": "subagent-driven-development",
    "parallel": "dispatching-parallel-agents",
    "skills": "using-superpowers",
    "superpowers": "using-superpowers",
    "bootstrap": "using-superpowers",
    "write-skill": "writing-skills",
}

_SKILL_CACHE = {"loaded": False, "skills": {}}


def _parse_frontmatter(text):
    """Ambil YAML frontmatter sederhana (name/description) dari SKILL.md."""
    meta, body = {}, text
    stripped = text.lstrip()
    if stripped.startswith("---"):
        end = stripped.find("\n---", 3)
        if end != -1:
            raw = stripped[3:end]
            body = stripped[end + 4:].lstrip("\n")
            key = None
            for line in raw.splitlines():
                m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
                if m:
                    key = m.group(1).strip()
                    meta[key] = m.group(2).strip().strip('"').strip("'")
                elif key and line.strip():
                    meta[key] = (meta[key] + " " + line.strip()).strip()
    return meta, body


def load_skills(force=False):
    """Muat semua skill dari folder skills/ (1 folder = 1 skill + resource-nya)."""
    if _SKILL_CACHE["loaded"] and not force:
        return _SKILL_CACHE["skills"]
    skills = {}
    if os.path.isdir(SKILLS_DIR):
        for entry in sorted(os.listdir(SKILLS_DIR)):
            sdir = os.path.join(SKILLS_DIR, entry)
            spath = os.path.join(sdir, "SKILL.md")
            if not os.path.isfile(spath):
                continue
            try:
                with open(spath, "r", errors="replace") as f:
                    text = f.read()
            except OSError:
                continue
            meta, body = _parse_frontmatter(text)
            resources = []
            for root, dirs, files in os.walk(sdir):
                dirs[:] = [d for d in sorted(dirs) if not d.startswith(".")]
                for fn in sorted(files):
                    if root == sdir and fn == "SKILL.md":
                        continue
                    rel = os.path.relpath(os.path.join(root, fn), sdir)
                    resources.append(rel.replace(os.sep, "/"))
            skills[entry] = {
                "key": entry,
                "name": meta.get("name", entry),
                "description": meta.get("description", "").strip(),
                "body": body.strip(),
                "dir": sdir,
                "resources": resources,
            }
    _SKILL_CACHE["loaded"] = True
    _SKILL_CACHE["skills"] = skills
    return skills


def resolve_skill(query):
    """Cari skill dari nama bebas: 'superpowers:tdd', 'TDD', 'test driven'…"""
    skills = load_skills()
    if not query:
        return None
    q = str(query).strip().lower()
    q = q.split(":")[-1] if ":" in q else q
    q = re.sub(r"[\s_]+", "-", q).strip("-")
    q = re.sub(r"(-skill|\.md)$", "", q)
    if q in skills:
        return skills[q]
    if q in SKILL_ALIASES and SKILL_ALIASES[q] in skills:
        return skills[SKILL_ALIASES[q]]
    for key in skills:
        if q and (q in key or key in q):
            return skills[key]
    words = [w for w in q.split("-") if len(w) > 3]
    for key, sk in skills.items():
        hay = (key + " " + sk["description"]).lower()
        if words and all(w in hay for w in words):
            return sk
    return None


def skills_index_text(max_desc=150):
    """Daftar skill (nama + deskripsi) buat ditempel di system prompt."""
    skills = load_skills()
    lines = []
    for key, sk in skills.items():
        desc = " ".join(sk["description"].split())
        if len(desc) > max_desc:
            desc = desc[:max_desc].rstrip() + "…"
        lines.append(f"- {key} — {desc}")
    return "\n".join(lines)


def bootstrap_skill_text():
    """Isi using-superpowers/SKILL.md — bootstrap yang bikin skill auto-trigger."""
    sk = load_skills().get("using-superpowers")
    return sk["body"] if sk else ""


# ---------------------------------------------------------------------------
# WORKFLOW LEDGER — catatan disiplin kerja untuk 1 tugas
# ---------------------------------------------------------------------------

TEST_PATH_RE = re.compile(
    r"(^|/)(tests?|spec|specs|__tests__)/|(^|/)test_[^/]+$|_test\.[A-Za-z0-9]+$"
    r"|\.test\.[A-Za-z0-9]+$|\.spec\.[A-Za-z0-9]+$|(^|/)[^/]*_spec\.[A-Za-z0-9]+$",
    re.IGNORECASE,
)

VERIFY_CMD_RE = re.compile(
    r"\b(pytest|unittest|jest|vitest|mocha|rspec|phpunit|tox|nox|ctest|shellcheck"
    r"|py_compile|mypy|ruff|flake8|pylint|eslint|tsc|gradle|mvn|dotnet|cargo|go)\b"
    r"|\bnpm\s+(run\s+)?test\b|\byarn\s+test\b|\bpnpm\s+(run\s+)?test\b"
    r"|\bmake\s+(test|check|lint)\b|\bbash\s+-n\b|\bnode\s+--check\b"
    r"|\bpython3?\s+-m\s+\w+",
    re.IGNORECASE,
)

SMOKE_CMD_RE = re.compile(
    r"\b(python3?|node|deno|bun|ruby|perl|php|go\s+run|java|bash|sh)\b\s+\S+",
    re.IGNORECASE,
)

# Perintah yang KELIHATANNYA verifikasi tapi sebenarnya gak ngebuktiin apa-apa.
# Tanpa ini, agent bisa "lolos" gate cuma dengan `python3 --version`.
FAKE_VERIFY_RE = re.compile(
    r"^\s*\S*\b(python3?|node|deno|bun|ruby|php|java|go|cargo|npm|yarn|pnpm)\b"
    r"\s+(--version|-V|--help|-h|version)\s*$"
    r"|^\s*(echo|true|:|cat|ls|pwd|cd|which|type|whoami|clear|touch|mkdir)\b",
    re.IGNORECASE,
)

# nama gate -> berapa kali boleh nge-block dalam 1 tugas (biar gak loop selamanya)
GATE_LIMITS = {
    "skill": 1,      # wajib invoke skill dulu (using-superpowers)
    "approval": 1,   # wajib approval manusia sebelum implementasi (brainstorming)
    "tdd": 1,        # wajib test dulu sebelum kode produksi (TDD)
    "plan": 1,       # wajib todo list sebelum bilang selesai (writing-plans)
    "verify": 2,     # wajib bukti verifikasi sebelum DONE (verification-before-completion)
    "review": 1,     # wajib self-review sebelum DONE (requesting-code-review)
}


ASSERT_RE = re.compile(
    r"\bassert\b|\bexpect\s*\(|\bshould\b|\.to(Be|Equal|Throw|Match)\b"
    r"|\bassertEqual\b|\bassertTrue\b|\bassertRaises\b|\bt\.Error\b|\bXCTAssert",
    re.IGNORECASE,
)


def _looks_like_real_test(content):
    """Test beneran minimal punya assertion. File kosong / cuma `pass` gak ngitung."""
    text = (content or "").strip()
    if len(text) < 20:
        return False
    return bool(ASSERT_RE.search(text))


class Workflow:
    """Ledger disiplin kerja: skill apa yang dipakai, approval, test, verifikasi."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.skills = []          # skill yang sudah dibaca
        self.todos = []           # [{"task":…, "status":…}]
        self.approvals = []       # jawaban manusia lewat ask_user
        self.writes = []          # file yang ditulis/diedit
        self.tests = []           # file test yang ditulis
        self.verifications = []   # perintah verifikasi yang benar-benar dijalankan
        self.reviews = 0          # berapa kali baca ulang file sendiri (self review)
        self.last_write_step = -1
        self.last_verify_step = -1
        self.step = 0
        self.fired = {}
        self.classification = None

    # -- pencatatan ---------------------------------------------------------
    def note_skill(self, key):
        if key not in self.skills:
            self.skills.append(key)
        if key == "brainstorming" and not self.classification:
            self.classification = "pending"

    def note_todos(self, todos):
        self.todos = todos

    def note_approval(self, question, answer):
        self.approvals.append({"q": question, "a": answer})

    def note_write(self, path, step, content=None):
        path = str(path).replace(os.sep, "/")
        if path not in self.writes:
            self.writes.append(path)
        if TEST_PATH_RE.search(path) and path not in self.tests:
            # File test kosong / cuma placeholder gak dihitung — itu ngakalin gate.
            if content is None or _looks_like_real_test(content):
                self.tests.append(path)
        self.last_write_step = step

    def note_bash(self, command, result, step):
        cmd = str(command)
        if FAKE_VERIFY_RE.search(cmd.strip()):
            return  # `python3 --version` / `echo ok` bukan bukti apa-apa
        looks_verify = bool(VERIFY_CMD_RE.search(cmd)) or bool(SMOKE_CMD_RE.search(cmd))
        failed = "[exit code:" in (result or "") or "[Error bash" in (result or "")
        if looks_verify and not failed:
            self.verifications.append({"cmd": cmd[:200], "step": step})
            self.last_verify_step = step
            if TEST_PATH_RE.search(cmd) or re.search(r"\b(pytest|jest|vitest|unittest|test)\b", cmd, re.I):
                if cmd not in self.tests:
                    self.tests.append(cmd)

    def note_read(self, path):
        self.reviews += 1

    # -- ringkasan ----------------------------------------------------------
    def has_pending_verification(self):
        return bool(self.writes) and self.last_verify_step < self.last_write_step

    def summary(self):
        return {
            "skills": list(self.skills),
            "todos": len(self.todos),
            "approvals": len(self.approvals),
            "files": len(self.writes),
            "tests": len(self.tests),
            "verifications": len(self.verifications),
        }

    def can_fire(self, gate):
        used = self.fired.get(gate, 0)
        if used >= GATE_LIMITS.get(gate, 1):
            return False
        self.fired[gate] = used + 1
        return True


WORKFLOW = Workflow()


def _gates_on(cfg):
    # Kalau folder skills/ gak ada (mis. user cuma nyalin main.py doang), gate
    # yang nyuruh "invoke skill" bakal mustahil dipenuhi. Jadi matikan aja —
    # agent tetap jalan mode polos, gak kejebak loop.
    if not load_skills():
        return False
    return bool(cfg.get("superpowers", True)) and bool(cfg.get("gates", True))


def pre_action_gate(tool_name, args, wf, cfg):
    """Gate SEBELUM aksi jalan. Nge-block write/edit kalau disiplinnya dilewatin.

    Return: pesan gate (string) kalau harus di-block, atau None kalau boleh lanjut.
    """
    if not _gates_on(cfg):
        return None
    if tool_name not in ("write_file", "edit_file"):
        return None

    path = str((args or {}).get("path", ""))

    # 1) using-superpowers: skill dulu sebelum aksi apa pun
    if not wf.skills and wf.can_fire("skill"):
        return (
            "GATE [using-superpowers] — DITOLAK, kamu belum baca skill apa pun.\n"
            "Aturannya: kalau ada 1% kemungkinan sebuah skill relevan, kamu WAJIB invoke skill itu "
            "SEBELUM aksi apa pun (termasuk sebelum nulis file).\n"
            "Langkah kamu sekarang: ACTION: skill dengan INPUT {\"name\": \"brainstorming\"} "
            "(kerjaan kreatif/bikin fitur) atau {\"name\": \"systematic-debugging\"} (benerin bug). "
            "Habis itu ikutin isinya."
        )

    # 2) brainstorming HARD-GATE: approval manusia sebelum implementasi
    if not wf.approvals and wf.can_fire("approval"):
        return (
            "GATE [brainstorming HARD-GATE] — DITOLAK, kamu belum dapat persetujuan manusia.\n"
            "Jangan nulis kode apa pun sebelum kamu bilang ke partner manusia kamu apa rencanamu "
            "DAN dia setuju. Ceremony-nya boleh kecil, gate-nya gak pernah kecil.\n"
            "Langkah kamu sekarang: ACTION: ask_user dengan INPUT berisi klasifikasi jalur "
            "(spike / bounded / architectural) + desain singkat: pendekatan, file yang disentuh, "
            "cara nge-test. Contoh: {\"question\": \"Rencana: <desain singkat>. Setuju?\", "
            "\"options\": [\"Setuju, lanjut\", \"Ubah dulu\"]}"
        )

    # 3) TDD: test dulu (RED) sebelum kode produksi
    is_test_file = bool(TEST_PATH_RE.search(path.replace(os.sep, "/")))
    if (
        tool_name == "write_file"
        and not is_test_file
        and not wf.tests
        and _looks_like_code(path)
        and wf.can_fire("tdd")
    ):
        return (
            "GATE [test-driven-development] — DITOLAK: NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST.\n"
            f"Kamu mau nulis kode produksi ({path}) tapi belum ada test yang kamu tulis & lihat GAGAL.\n"
            "Langkah kamu sekarang: (1) write_file test-nya dulu (mis. test_xxx.py / xxx.test.js), "
            "(2) jalanin lewat bash dan LIHAT dia MERAH/gagal, (3) baru tulis kode minimal biar HIJAU.\n"
            "Kalau ini beneran gak bisa di-test (config, aset statis, dokumen, prototipe buangan), "
            "bilang alasannya di THINK lalu lanjut — gate ini cuma sekali."
        )
    return None


CODE_EXT = (
    ".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".go", ".rs", ".rb",
    ".java", ".kt", ".php", ".c", ".h", ".cpp", ".hpp", ".cs", ".swift", ".sh",
    ".bash", ".pl", ".lua", ".dart", ".scala", ".ex", ".exs",
)


def _looks_like_code(path):
    return str(path).lower().endswith(CODE_EXT)


def pre_done_gate(wf, cfg):
    """Gate SEBELUM agent boleh bilang DONE. Return pesan gate atau None."""
    if not _gates_on(cfg):
        return None

    # 1) skill sama sekali gak dipakai
    if not wf.skills and wf.can_fire("skill"):
        return (
            "GATE [using-superpowers] — BELUM SELESAI. Kamu ngerjain tugas ini tanpa invoke skill "
            "satu pun. Invoke skill yang relevan dulu (ACTION: skill), ikutin isinya, baru DONE."
        )

    if not wf.writes:
        # tugas tanya-jawab/riset: cukup pastikan skill dipakai
        return None

    # 2) writing-plans: kerjaan multi-langkah wajib punya todo list yang kelar
    if not wf.todos and wf.can_fire("plan"):
        return (
            "GATE [writing-plans] — BELUM SELESAI. Kamu nyentuh "
            f"{len(wf.writes)} file tanpa rencana yang kelihatan.\n"
            "Langkah kamu sekarang: ACTION: todo_write — pecah kerjaan jadi task kecil "
            "dan tandai mana yang sudah beres, biar partner manusia kamu bisa ngecek."
        )

    # 3) verification-before-completion: NO COMPLETION CLAIMS WITHOUT FRESH EVIDENCE
    if wf.has_pending_verification() and wf.can_fire("verify"):
        changed = ", ".join(wf.writes[-5:])
        return (
            "GATE [verification-before-completion] — DITOLAK.\n"
            "THE IRON LAW: NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE.\n"
            f"Kamu ngubah file ({changed}) sesudah verifikasi terakhir. Kalau kamu belum jalanin "
            "perintah verifikasinya DI LANGKAH INI, kamu gak boleh bilang selesai.\n"
            "Langkah kamu sekarang: ACTION: bash — jalanin test/build/lint/syntax check yang "
            "beneran (mis. python3 -m pytest, python3 -m py_compile file.py, node --check file.js, "
            "npm test), BACA outputnya, baru DONE dengan menyertakan buktinya."
        )

    # 4) self review sebelum ngaku beres
    if wf.reviews == 0 and wf.can_fire("review"):
        return (
            "GATE [requesting-code-review] — BELUM SELESAI. Kamu belum baca ulang hasil kerjamu "
            "sendiri. Langkah kamu sekarang: ACTION: read_file file yang kamu ubah, cek beneran "
            "sesuai permintaan (gak ada TODO nyangkut, gak ada kode setengah jadi), baru DONE."
        )
    return None


def workflow_record(tool_name, args, result, wf, step):
    """Catat efek 1 aksi ke ledger disiplin kerja."""
    args = args or {}
    if tool_name == "skill":
        sk = resolve_skill(args.get("name") or args.get("skill") or "")
        if sk:
            wf.note_skill(sk["key"])
    elif tool_name in ("write_file", "edit_file"):
        if not str(result).startswith("[Error"):
            body = args.get("content") if tool_name == "write_file" else args.get("new")
            wf.note_write(args.get("path", "?"), step, content=body)
    elif tool_name == "bash":
        wf.note_bash(args.get("command", ""), result, step)
    elif tool_name == "read_file":
        wf.note_read(args.get("path", ""))
    elif tool_name == "todo_write":
        pass  # dicatat langsung di tool-nya


# ---------------------------------------------------------------------------
# TOOLS SUPERPOWERS
# ---------------------------------------------------------------------------

def tool_list_skills(args, cfg):
    skills = load_skills()
    if not skills:
        return ("[Error list_skills: folder skills/ kosong. Pastikan kamu `git clone` "
                "repo-nya lengkap, bukan cuma main.py.]")
    lines = [f"{len(skills)} skill Superpowers tersedia (pakai tool `skill` buat baca):", ""]
    for key, sk in skills.items():
        lines.append(f"- {key}: {' '.join(sk['description'].split())}")
        if sk["resources"]:
            lines.append(f"    resource: {', '.join(sk['resources'])}")
    return "\n".join(lines)


def tool_skill(args, cfg):
    """Baca isi 1 skill (atau resource di dalamnya) — progressive disclosure."""
    name = args.get("name") or args.get("skill") or args.get("query") or ""
    sk = resolve_skill(name)
    if not sk:
        avail = ", ".join(load_skills().keys()) or "(kosong)"
        return f"[Error skill: '{name}' gak ketemu. Yang ada: {avail}]"

    resource = (args.get("resource") or args.get("file") or "").strip()
    if resource:
        rel = resource.replace("\\", "/").lstrip("/")
        full = os.path.abspath(os.path.join(sk["dir"], rel))
        if not full.startswith(os.path.abspath(sk["dir"])) or not os.path.isfile(full):
            return (f"[Error skill: resource '{resource}' gak ada di skill {sk['key']}. "
                    f"Yang ada: {', '.join(sk['resources']) or '-'}]")
        try:
            with open(full, "r", errors="replace") as f:
                text = f.read()
        except OSError as e:
            return f"[Error skill: gagal baca resource ({e})]"
        return f"=== SKILL {sk['key']} / {rel} ===\n{text.strip()}"

    body = sk["body"]
    extra = ""
    if sk["resources"]:
        extra = ("\n\nRESOURCE TAMBAHAN (baca dengan ACTION: skill "
                 f"INPUT {{\"name\": \"{sk['key']}\", \"resource\": \"<nama>\"}}):\n- "
                 + "\n- ".join(sk["resources"]))
    return (
        f"=== SKILL: {sk['key']} ===\n"
        f"{sk['description']}\n\n"
        f"{body}{extra}\n\n"
        f"[Kamu sudah invoke skill '{sk['key']}'. Umumkan 'Using {sk['key']} to <tujuan>' "
        f"di THINK berikutnya, dan IKUTI isinya persis — kalau ada checklist, bikin todo per item.]"
    )


def _normalize_todos(raw):
    todos = []
    if isinstance(raw, str):
        raw = [line.strip("-* ").strip() for line in raw.splitlines() if line.strip()]
    if not isinstance(raw, list):
        return todos
    for item in raw:
        if isinstance(item, str):
            todos.append({"task": item.strip(), "status": "pending"})
        elif isinstance(item, dict):
            task = item.get("task") or item.get("content") or item.get("title") or ""
            status = str(item.get("status", "pending")).lower().strip()
            if status in ("in progress", "in-progress", "doing", "wip", "aktif"):
                status = "in_progress"
            elif status in ("done", "complete", "completed", "selesai", "beres"):
                status = "done"
            elif status in ("blocked", "stuck", "macet"):
                status = "blocked"
            else:
                status = "pending"
            if task:
                todos.append({"task": str(task).strip(), "status": status})
    return todos


def tool_todo_write(args, cfg):
    """Bikin / update checklist tugas (kelihatan di terminal, kayak Claude Code)."""
    todos = _normalize_todos(args.get("todos") or args.get("items") or args.get("tasks"))
    if not todos:
        return "[Error todo_write: 'todos' wajib diisi, contoh {\"todos\":[{\"task\":\"...\",\"status\":\"pending\"}]}]"
    WORKFLOW.note_todos(todos)
    todo_panel(todos)
    done = sum(1 for t in todos if t["status"] == "done")
    return (f"[OK] Checklist diperbarui: {done}/{len(todos)} beres.\n"
            + "\n".join(f"  [{'x' if t['status'] == 'done' else ' '}] {t['task']} ({t['status']})"
                        for t in todos))


def tool_ask_user(args, cfg):
    """Tanya / minta persetujuan ke partner manusia — gate approval Superpowers."""
    question = str(args.get("question") or args.get("prompt") or "").strip()
    if not question:
        return "[Error ask_user: 'question' wajib diisi]"
    options = args.get("options") or []
    if isinstance(options, str):
        options = [o.strip() for o in options.split("|") if o.strip()]
    options = [str(o) for o in options if str(o).strip()][:6]

    question_panel(question, options)
    if not sys.stdin or not sys.stdin.isatty():
        WORKFLOW.note_approval(question, "[non-interaktif: dianggap setuju]")
        return ("[OK] Mode non-interaktif (stdin bukan terminal) — dianggap SETUJU. "
                "Lanjut, tapi tetap catat asumsimu di ringkasan akhir.")
    try:
        answer = input(f"{FG_CYAN}{BOLD}Jawab ›{RESET} ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        WORKFLOW.note_approval(question, "[dibatalkan]")
        return "[OK] Partner manusia gak jawab (batal). Berhenti dan tanya lagi nanti."
    if not answer:
        answer = options[0] if options else "(setuju)"
    if re.fullmatch(r"[1-9]", answer) and options and int(answer) <= len(options):
        answer = options[int(answer) - 1]
    WORKFLOW.note_approval(question, answer)
    print()
    return (f"[OK] Jawaban partner manusia: {answer}\n"
            "[Gate approval terpenuhi. Kerjakan PERSIS yang disetujui — kalau jawabannya minta "
            "perubahan, revisi dulu rencananya dan tanya lagi.]")


TOOLS = {
    "list_files": tool_list_files,
    "grep_files": tool_grep_files,
    "read_file": tool_read_file,
    "write_file": tool_write_file,
    "edit_file": tool_edit_file,
    "bash": tool_bash,
    "web_search": tool_web_search,
    "web_fetch": tool_web_fetch,
    # --- superpowers ---
    "skill": tool_skill,
    "list_skills": tool_list_skills,
    "todo_write": tool_todo_write,
    "ask_user": tool_ask_user,
}


# ============================================================================
# AGENT: prompt sistem, parser respons, loop THINK -> ACTION -> OBSERVATION
# ============================================================================

BASE_SYSTEM_PROMPT = """Kamu adalah coding agent SUPER POWER ala opencode / Claude Code yang jalan di terminal. Kamu punya akses penuh ke bash, file system workspace, DAN web (DuckDuckGo / SearXNG). Kamu kerja bareng seorang PARTNER MANUSIA — bukan buat dia, tapi SAMA dia.

ATURAN RESPONS — balas HANYA dengan pola berikut, tanpa teks lain di luar pola:

THINK: <rencana singkat 1-3 kalimat>          (opsional tapi dianjurkan)

ACTION: <nama_tool>
INPUT: <json satu baris>

atau kalau tugas sudah selesai:

DONE: <jawaban / ringkasan final>

Satu ACTION per balasan. Tunggu OBSERVATION sebelum lanjut.

TOOLS:
- skill       {"name": "brainstorming", "resource": ""}   BACA skill Superpowers (WAJIB, lihat bagian di bawah)
- list_skills {}                                 lihat semua skill yang tersedia
- todo_write  {"todos": [{"task": "...", "status": "pending|in_progress|done|blocked"}]}  checklist kerja
- ask_user    {"question": "...", "options": ["Setuju", "Ubah dulu"]}   TANYA / minta persetujuan partner manusia
- list_files  {"path": ".", "depth": 3}          jelajah isi folder (+ ukuran file)
- grep_files  {"pattern": "...", "path": ".", "regex": false, "limit": 50}  cari teks di banyak file
- read_file   {"path": "...", "offset": 0, "limit": 0}   baca file (bisa per-baris)
- write_file  {"path": "...", "content": "..."}
- edit_file   {"path": "...", "old": "...", "new": "..."}   pencocokan fuzzy, toleran whitespace
- bash        {"command": "...", "timeout": 120}   jalankan apa pun (maks 600 dtk, cwd=workspace)
- web_search  {"query": "...", "limit": 5, "engine": "auto|ddg|searxng"}   cari info terkini
- web_fetch   {"url": "https://..."}             baca isi halaman web

=============================================================================
SUPERPOWERS — INI BUKAN OPSIONAL
=============================================================================
Kamu bukan agent yang langsung nyemplung ngoding. Kamu punya SKILL LIBRARY berisi
metodologi kerja yang sudah teruji. Skill = disiplin, bukan saran.

{bootstrap}

SKILL YANG TERSEDIA (baca pakai ACTION: skill):
{index}

CARA PAKAI SKILL (progressive disclosure):
Kamu cuma lihat NAMA + DESKRIPSI di atas. Isi lengkapnya kamu baca on-demand:
    ACTION: skill
    INPUT: {"name": "brainstorming"}
Habis itu umumkan di THINK: "Using brainstorming to <tujuan>", lalu IKUTI ISINYA
PERSIS. Kalau skill-nya punya checklist, bikin todo_write satu item per langkah.

Skill punya resource tambahan yang dirujuk di dalamnya. Baca gitu juga:
    INPUT: {"name": "test-driven-development", "resource": "writing-good-tests.md"}

PENTING — ADAPTASI HARNESS:
Skill Superpowers ditulis buat harness yang punya subagent. Harness INI belum
punya. Baca ini SEKALI di awal biar kamu gak salah pakai skill:
    INPUT: {"name": "using-superpowers", "resource": "references/agent-cli-tools.md"}
Intinya: skill subagent-driven-development & dispatching-parallel-agents GAK BISA
dipakai apa adanya — pakai executing-plans dan review sendiri. JANGAN pura-pura
punya subagent, JANGAN ngarang hasil review dari "agent lain".

=============================================================================
ALUR KERJA WAJIB (SOP)
=============================================================================
0. SKILL CHECK — SEBELUM aksi apa pun (termasuk sebelum nanya, sebelum list_files):
   pikir "skill mana yang relevan?" lalu invoke. Kalau peluangnya cuma 1% pun, invoke.
   - "bikin/tambah/ubah fitur"  -> skill brainstorming DULU
   - "ada bug / error / gagal"  -> skill systematic-debugging DULU
   - "punya spec, bikin plan"   -> skill writing-plans
   - "mau ngoding"              -> skill test-driven-development
   - "mau bilang selesai"       -> skill verification-before-completion

1. BRAINSTORM & APPROVAL GATE — klasifikasikan dulu: spike / bounded / architectural.
   Sampaikan klasifikasinya. Tanya hal yang penting SATU per satu pakai ask_user.
   Lalu presentasikan desain singkat (pendekatan, file yang disentuh, cara nge-test)
   dan MINTA PERSETUJUAN pakai ask_user. JANGAN nulis kode sebelum dia bilang iya.
   Ceremony boleh kecil buat tugas kecil — GATE APPROVAL-nya gak pernah kecil.

2. RENCANA — todo_write: pecah jadi task kecil. Update statusnya sambil jalan
   (in_progress -> done). Partner manusia kamu harus bisa lihat progresnya.

3. EKSPLORASI & RISET — list_files/grep_files/read_file dulu, JANGAN nebak isi file.
   Butuh fakta terkini/versi library/API? web_search lalu web_fetch, baru simpulkan.

4. TDD — THE IRON LAW: NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST.
   RED: tulis test-nya dulu -> jalanin lewat bash -> LIHAT DIA GAGAL (wajib, dan
   gagalnya harus karena fiturnya belum ada, bukan karena typo).
   GREEN: tulis kode paling minimal biar lulus -> jalanin -> lihat HIJAU.
   REFACTOR: rapikan, tetap hijau. Ulangi buat perilaku berikutnya.
   Nulis kode duluan? Hapus, mulai lagi dari test.

5. DEBUG SISTEMATIS — NO FIXES WITHOUT ROOT CAUSE FIRST. Baca error-nya beneran,
   bikin reproduksi terkecil, telusuri sampai akar, baru perbaiki. Nambal gejala =
   gagal. Kalau nebak-nebak 2x gak jalan, berhenti nebak dan investigasi beneran.

6. VERIFIKASI — NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE.
   Sebelum ngaku beres: jalanin perintah buktinya (pytest / npm test / py_compile /
   node --check / build / lint), BACA outputnya, cek exit code. Belum jalanin di
   langkah ini = belum boleh ngaku lulus. Dilarang bilang "harusnya sih jalan".

7. SELF-REVIEW — read_file lagi hasil kerjamu. Cek satu-satu ke permintaan awal:
   ada TODO nyangkut? ada kode setengah jadi? ada yang kelewat? Perbaiki dulu.

8. DONE — ringkasan + daftar file + BUKTI verifikasi (perintah yang kamu jalanin +
   hasilnya) + sumber [1](url) kalau pakai info web.

=============================================================================
RED FLAGS — kalau pikiran ini muncul, kamu lagi cari pembenaran. BERHENTI.
=============================================================================
| Pikiran                              | Kenyataan                                    |
| "Ini gampang, gak usah pakai skill"  | Yang gampang sering berubah rumit. Invoke.   |
| "Aku ngerti maksudnya kok"           | Ngerti konsep != pakai skill. Baca skill-nya.|
| "Aku cek file dulu deh"              | Skill yang ngatur CARA ngecek. Skill duluan. |
| "Terlalu sederhana buat minta izin"  | Desainnya boleh 2 kalimat. Approval tetap wajib.|
| "Sekali ini aja skip TDD"            | Gak ada pengecualian tanpa izin partner.     |
| "Nanti aja test-nya"                 | Test sesudah kode langsung lulus = gak bukti apa-apa.|
| "Harusnya udah jalan sih"            | JALANIN perintahnya. Yakin != bukti.         |
| "Linter lulus, berarti aman"         | Linter bukan compiler, bukan test.           |
| "Udah aku tes manual tadi"           | Manual gak bisa diulang. Bikin test otomatis.|
| "Sayang kalau kode ini dihapus"      | Sunk cost. Kode yang gak dipercaya = beban.  |

ATURAN TAMBAHAN:
- Jangan menyerah kalau bash error — baca outputnya, cari akarnya, perbaiki.
- JSON INPUT harus valid (pakai \\n untuk newline di dalam string).
- Kalau gate (🛑 GATE [...]) muncul di OBSERVATION, itu disiplin Superpowers nge-block
  kamu. JANGAN diakalin — kerjain persis yang dia minta, baru lanjut.
- Jujur soal ketidakpastian. Lebih baik bilang "belum kebukti" daripada ngarang.
- Jawab pakai bahasa yang dipakai user (default Indonesia).

Instruksi langsung dari partner manusia menang di atas skill; skill menang di atas
kebiasaan default kamu. Skip alur cuma kalau dia yang bilang skip."""


LEAN_SYSTEM_PROMPT = """Kamu adalah coding agent ala opencode / Claude Code di terminal, dengan akses bash, file workspace, dan web.

ATURAN RESPONS — balas HANYA dengan pola berikut:

THINK: <rencana singkat>

ACTION: <nama_tool>
INPUT: <json satu baris>

atau kalau selesai:

DONE: <ringkasan final>

TOOLS: list_files {"path":".","depth":3} · grep_files {"pattern":"...","path":"."} · read_file {"path":"...","offset":0,"limit":0} · write_file {"path":"...","content":"..."} · edit_file {"path":"...","old":"...","new":"..."} · bash {"command":"...","timeout":120} · web_search {"query":"...","limit":5} · web_fetch {"url":"..."} · todo_write {"todos":[...]} · ask_user {"question":"...","options":[...]} · skill {"name":"..."} · list_skills {}

ALUR: THINK -> eksplorasi (jangan nebak isi file) -> riset web kalau perlu ->
bikin/edit -> JALANIN & TEST pakai bash -> baca ulang hasilnya -> DONE dengan
ringkasan + daftar file + sumber [1](url) kalau pakai info web.

Jangan menyerah kalau bash error — baca pesannya, perbaiki, ulangi.
JSON INPUT harus valid. Jawab pakai bahasa user (default Indonesia).

[Mode Superpowers OFF — nyalakan lagi dengan /superpowers on buat dapat metodologi
brainstorm -> approval -> plan -> TDD -> verifikasi.]"""


def build_system_prompt(cfg):
    """Rakit system prompt. Superpowers ON = skill library + SOP + gates."""
    if not cfg.get("superpowers", True) or not load_skills():
        return LEAN_SYSTEM_PROMPT
    index = skills_index_text()
    # NB: sengaja pakai replace, BUKAN .format() — prompt-nya penuh contoh JSON
    # berkurung kurawal ({"name": ...}) yang bakal bikin .format() meledak.
    return (
        BASE_SYSTEM_PROMPT
        .replace("{bootstrap}", bootstrap_skill_text() or "")
        .replace("{index}", index)
    )


# dipertahankan buat kompatibilitas / debugging manual
SYSTEM_PROMPT = BASE_SYSTEM_PROMPT


def parse_response(text):
    thinks = [
        t.strip()
        for t in re.findall(
            r"^[\s*]*(?:THINK(?:ING)?):\s*\**\s*(.*?)(?=^[\s*]*(?:THINK(?:ING)?|ACTION|DONE):|\Z)",
            text,
            flags=re.DOTALL | re.MULTILINE,
        )
        if t.strip()
    ]

    done = re.search(r"^[\s*]*DONE:\s*\**\s*(.*)", text, flags=re.DOTALL | re.MULTILINE)
    if done:
        return {"kind": "done", "summary": done.group(1).strip(), "thinks": thinks}

    m = re.search(
        r"^[\s*]*ACTION:\s*\**\s*([A-Za-z_][A-Za-z0-9_]*)\s*\n\s*INPUT:\s*(.*)",
        text, flags=re.DOTALL | re.MULTILINE,
    )
    if not m:
        m = re.search(
            r"^[\s*]*ACTION:\s*\**\s*([A-Za-z_][A-Za-z0-9_]*)\s+INPUT:\s*(.*)",
            text, flags=re.DOTALL | re.MULTILINE,
        )
    if not m:
        return {
            "kind": "error",
            "error": "AI tidak mengikuti format (butuh ACTION+INPUT atau DONE)",
            "thinks": thinks,
        }

    tool_name = m.group(1).strip()
    raw = m.group(2).strip()
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw).strip()
    args, err = None, None
    try:
        args = json.loads(raw)
    except ValueError:
        idx = raw.rfind("}")
        if idx != -1:
            try:
                args = json.loads(raw[: idx + 1])
            except ValueError as e:
                err = str(e)
        else:
            err = "tidak ada JSON"
    if not isinstance(args, dict):
        return {
            "kind": "error",
            "error": f"Format INPUT bukan JSON valid ({err or 'tidak dikenali'})",
            "thinks": thinks,
        }
    return {"kind": "action", "tool": tool_name, "args": args, "thinks": thinks}


HELP_TEXT = """Perintah yang tersedia:
  /help                          Tampilkan bantuan ini
  /skills                        🦸 Lihat semua skill Superpowers yang dimuat
  /skills <nama>                 Baca isi 1 skill, contoh: /skills tdd
  /doctor                        🩺 Cek instalasi (kalau ada yang aneh)
  /superpowers                   Status metodologi Superpowers
  /superpowers on|off            Nyalakan / matikan metodologi (SOP + skill)
  /superpowers gates on|off      Gate keras (approval, TDD, verifikasi) on/off
  /intro                         Putar ulang animasi pembuka (matrix + loading)
  /connect                       Setup / cek koneksi API (template Xkiro.com)
  /connect show|test             Lihat / tes koneksi saat ini
  /models                        Lihat semua model yang tersedia
  /model <no|nama>               Ganti model aktif, contoh: /model kimik3
  /think on|off                  Aktifkan / matikan reasoning (thinking) model
  /think show|hide|toggle        Buka / tutup tampilan blok thinking
  /effort <level>                Level upaya: none,low,medium,high,xhigh,max
  /search                        Lihat pengaturan AI search (DDG / SearXNG)
  /search ddg|auto               Pilih engine: DDG saja, atau auto (SearXNG kalau di-set)
  /search searxng <url>          Pakai instance SearXNG sendiri di URL tsb
  /search searxng off            Matikan SearXNG (balik ke DDG)
  /search test <query>           Coba cari <query> langsung (5 hasil)
  /fetch <url>                   Coba ambil isi halaman web <url>
  /download -f <file>            ZIP file hasil kerja agent (dari tugas terakhir)
  /download                      ZIP SEMUA file yang dibuat di tugas terakhir
  /download list                 Lihat daftar file yang bisa di-download
  /limit <n>                     Maks. langkah agent per tugas (default 40)
  /status                        Tampilkan status lengkap
  /clear                         Kosongkan riwayat percakapan
  /exit atau /quit               Keluar dari program

Selain itu, ketik pesan biasa untuk kasih tugas ke agent.

🦸 SUPERPOWERS (aktif secara default): agent gak langsung nyemplung ngoding. Dia
   dipaksa lewat SOP: baca skill -> brainstorm & minta persetujuan kamu -> bikin
   rencana (todo) -> TDD (test dulu, lihat MERAH, baru kode) -> jalanin bukti
   verifikasi -> baca ulang hasilnya -> baru boleh bilang DONE.
   Kalau dia nyalip alur, muncul 🛑 GATE dan aksinya di-block.

Awali dengan '!' buat jalankan bash langsung, contoh: !ls -la"""


class State:
    def __init__(self):
        self.config = load_config()
        self.model = get_model_by_key(self.config.get("default_model_key", DEFAULT_MODEL_KEY))
        self.thinking_on = bool(self.config.get("thinking", True))
        self.show_thinking = bool(self.config.get("show_thinking", True))
        self.effort = closest_supported_effort(
            self.model, self.config.get("default_effort", self.model["default_effort"])
        )
        try:
            self.max_steps = max(1, min(200, int(self.config.get("max_steps", 30))))
        except (TypeError, ValueError):
            self.max_steps = 30
        self.step_count = 0
        self.messages = []  # riwayat role/content yang dikirim ke model


def print_models():
    system_line("Model yang tersedia lewat Xkiro.com:", FG_CYAN)
    for i, m in enumerate(MODEL_CATALOG, start=1):
        efforts = ", ".join(m["efforts"])
        print(
            f"  {BOLD}{i:>2}.{RESET} {m['label']:<18} "
            f"{DIM}({m['id']}){RESET}  {FG_YELLOW}upaya: {efforts}{RESET}"
        )
    print()


def _print_search_results(text):
    lines = text.splitlines()
    if lines:
        print(f"{DIM}{FG_GREY}  ↳ {FG_YELLOW}{lines[0]}{RESET}")
        for line in lines[1:]:
            if not line.strip():
                continue
            print(f"{DIM}{FG_GREY}    {line}{RESET}")
    print()


DOWNLOADS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")


def _resolve_ws_file(name):
    """Cari file di workspace: relatif, atau absolut selama masih di dalam workspace."""
    cand = os.path.abspath(os.path.join(WORKSPACE_DIR, name))
    if os.path.isfile(cand):
        return cand
    cand = os.path.abspath(name)
    if cand.startswith(WORKSPACE_DIR) and os.path.isfile(cand):
        return cand
    return None


def handle_download(rest):
    """/download [-f <file>] [list]  — zip file hasil kerja agent ke folder downloads/."""
    arg = rest.strip()
    if arg == "list":
        if not LAST_TASK_FILES:
            system_line("Belum ada file yang dibuat di tugas terakhir.", FG_YELLOW)
            system_line("Pakai: /download -f <nama file di workspace>")
            return
        system_line("📦 File hasil kerja terakhir (workspace/):", FG_CYAN)
        for i, f in enumerate(LAST_TASK_FILES, 1):
            full = os.path.join(WORKSPACE_DIR, f)
            size = os.path.getsize(full) if os.path.isfile(full) else 0
            print(f"  {BOLD}{i}.{RESET} {f}  {DIM}({size:,} B){RESET}")
        print()
        return

    if arg.startswith("-f"):
        fname = arg[2:].strip().strip('"').strip("'")
        if not fname:
            error_line("Pakai: /download -f <nama file>")
            return
        files = [fname]
        single = True
    elif arg in ("", "all"):
        if not LAST_TASK_FILES:
            error_line("Belum ada file yang dibuat di tugas terakhir.")
            system_line("Pakai: /download -f <nama file>  (lihat /download list buat daftar)")
            return
        files = list(LAST_TASK_FILES)
        single = False
    else:
        error_line(f"Argumen '{arg}' tidak dikenal. Pakai: /download -f <file> | /download | /download list")
        return

    resolved = []
    for name in files:
        full = _resolve_ws_file(name)
        if not full:
            error_line(f"File '{name}' tidak ditemukan di workspace/.")
            system_line("Cek dulu: /download list")
            return
        resolved.append(full)

    os.makedirs(DOWNLOADS_DIR, exist_ok=True)
    if single:
        zip_name = f"{os.path.basename(resolved[0])}.zip"
        arc = os.path.basename(resolved[0])
    else:
        zip_name = f"agent-files-{time.strftime('%Y%m%d-%H%M%S')}.zip"
        arc = None
    zip_path = os.path.join(DOWNLOADS_DIR, zip_name)
    if os.path.exists(zip_path):
        zip_name = zip_name.replace(".zip", f"-{time.strftime('%H%M%S')}.zip")
        zip_path = os.path.join(DOWNLOADS_DIR, zip_name)

    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for full in resolved:
                zf.write(full, arcname=arc or os.path.relpath(full, WORKSPACE_DIR).replace(os.sep, "/"))
    except Exception as e:
        error_line(f"Gagal bikin zip: {e}")
        return

    size_kb = os.path.getsize(zip_path) / 1024
    rel = os.path.relpath(zip_path, os.path.dirname(os.path.abspath(__file__)))
    success_line(f"💾 Download siap: {rel} ({size_kb:.1f} KB)")
    system_line(f"{DIM}  Isi: {', '.join(os.path.relpath(f, WORKSPACE_DIR) for f in resolved)}{RESET}")
    print()


def handle_skills(rest):
    """/skills — lihat daftar skill; /skills <nama> — baca isinya."""
    arg = rest.strip()
    skills = load_skills()
    if not skills:
        error_line("Folder skills/ kosong atau gak ketemu.")
        system_line(f"Lokasi yang dicari: {SKILLS_DIR}")
        system_line("Pastikan kamu clone repo-nya lengkap: git clone https://github.com/EdwardsVD/Agent.git")
        return

    if not arg:
        w = term_width()
        print(f"{BG_DARKGREY}{FG_CYAN}{BOLD}{f' 🦸 Superpowers — {len(skills)} skill '.ljust(w)}{RESET}")
        for key, sk in skills.items():
            desc = " ".join(sk["description"].split())
            print(f"  {FG_CYAN}{BOLD}{key}{RESET}")
            for line in _wrap_lines(desc, w - 6):
                print(f"      {DIM}{line}{RESET}")
        print()
        system_line("Baca isinya: /skills <nama>   contoh: /skills tdd", FG_YELLOW)
        system_line("Agent otomatis baca sendiri sesuai kebutuhan (progressive disclosure).", FG_GREY)
        print()
        return

    parts = arg.split(None, 1)
    sk = resolve_skill(parts[0])
    if not sk:
        error_line(f"Skill '{parts[0]}' gak ketemu.")
        system_line("Lihat semua: /skills")
        return
    resource = parts[1].strip() if len(parts) > 1 else ""
    out = tool_skill({"name": sk["key"], "resource": resource}, {})
    w = term_width()
    print(f"{FG_CYAN}{BOLD}{'─' * w}{RESET}")
    print(out)
    print(f"{FG_CYAN}{BOLD}{'─' * w}{RESET}\n")


def handle_superpowers(rest, state):
    """/superpowers [on|off|gates on|gates off|status]"""
    arg = rest.strip().lower()
    cfg = state.config

    def _show():
        n = len(load_skills())
        if not n:
            error_line("Folder skills/ gak ketemu — Superpowers OTOMATIS MATI.")
            system_line(f"   Dicari di: {SKILLS_DIR}", FG_YELLOW)
            system_line("   Fix: clone repo-nya lengkap, jangan cuma main.py —", FG_YELLOW)
            system_line("        git clone https://github.com/EdwardsVD/Agent.git", FG_YELLOW)
            print()
            return
        sp = cfg.get("superpowers", True)
        gt = cfg.get("gates", True)
        system_line(
            f"🦸 Superpowers : {'ON' if sp else 'OFF'}\n"
            f"   Gates       : {'ON' if gt else 'OFF'}  "
            f"(approval · TDD · verifikasi · self-review)\n"
            f"   Skill dimuat: {len(load_skills())} dari {SKILLS_DIR}",
            FG_CYAN,
        )
        if sp:
            system_line(
                "   Agent dipaksa: skill check → brainstorm+approval → rencana → "
                "TDD → verifikasi bukti → self-review → baru DONE.", FG_GREY)
        else:
            system_line("   Mode polos: agent langsung eksekusi tanpa metodologi.", FG_GREY)
        print()

    if arg in ("", "status"):
        _show()
        return
    if arg in ("on", "aktif", "nyala"):
        cfg["superpowers"] = True
        cfg["gates"] = True
        save_config(cfg)
        success_line("Superpowers ON — metodologi + gate keras aktif.")
        _show()
        return
    if arg in ("off", "mati"):
        cfg["superpowers"] = False
        save_config(cfg)
        system_line("Superpowers OFF — agent balik jadi mode polos.", FG_YELLOW)
        _show()
        return
    if arg.startswith("gates"):
        val = arg[5:].strip()
        if val in ("on", "aktif", "nyala"):
            cfg["gates"] = True
            save_config(cfg)
            success_line("Gates ON — agent bakal di-block kalau nyalip alur.")
        elif val in ("off", "mati"):
            cfg["gates"] = False
            save_config(cfg)
            system_line("Gates OFF — SOP tetap di prompt, tapi gak dipaksa keras.", FG_YELLOW)
        else:
            error_line("Pakai: /superpowers gates on|off")
            return
        _show()
        return
    if arg in ("reload", "muat"):
        n = len(load_skills(force=True))
        success_line(f"{n} skill dimuat ulang dari {SKILLS_DIR}")
        return
    error_line(f"Argumen '{arg}' gak dikenal. Pakai: /superpowers on|off|gates on|gates off|reload|status")


def handle_slash_command(cmd, state):
    """Return True kalau program harus berhenti."""
    parts = cmd.strip().split(maxsplit=1)
    name = parts[0].lower()
    rest = parts[1].strip() if len(parts) > 1 else ""

    if name in ("/exit", "/quit"):
        system_line("Sampai jumpa!", FG_CYAN)
        return True

    if name == "/intro":
        intro_animation()
        banner()
        return False

    if name in ("/download", "/d"):
        handle_download(rest)
        return False

    if name in ("/skills", "/skill"):
        handle_skills(rest)
        return False

    if name in ("/doctor", "/dok"):
        doctor()
        return False

    if name in ("/superpowers", "/sp"):
        handle_superpowers(rest, state)
        return False

    if name == "/help":
        system_line(HELP_TEXT)
        return False

    if name == "/status":
        cfg = state.config
        engine = cfg.get("search_engine", "auto")
        if engine == "auto":
            engine = "auto → SearXNG" if cfg.get("searxng_url") else "auto → DDG"
        key = cfg.get("api_key", "")
        key_disp = (
            (key[:4] + "…" + key[-4:])
            if key and len(key) > 8
            else ("(kosong)" if not key else "****")
        )
        system_line(
            f"model        : {state.model['label']} ({state.model['id']})\n"
            f"effort       : {'OFF' if not state.thinking_on else state.effort.upper()}\n"
            f"thinking     : {'ON · TAMPIL' if (state.thinking_on and state.show_thinking) else ('ON · SEMBUNYI' if state.thinking_on else 'OFF')}\n"
            f"search       : {engine}  |  SearXNG: {cfg.get('searxng_url') or '(belum di-set)'}\n"
            f"max steps    : {state.max_steps}\n"
            f"superpowers  : {'ON' if cfg.get('superpowers', True) else 'OFF'}"
            f"  |  gates: {'ON' if cfg.get('gates', True) else 'OFF'}"
            f"  |  {len(load_skills())} skill dimuat\n"
            f"endpoint     : {cfg.get('base_url')}\n"
            f"api key      : {key_disp}\n"
            f"config file  : {CONFIG_PATH}"
        )
        return False

    if name == "/clear":
        state.messages = []
        state.step_count = 0
        success_line("Riwayat percakapan dikosongkan.")
        return False

    if name == "/models":
        print_models()
        return False

    if name == "/model":
        if not rest:
            print_models()
            system_line("Pakai: /model <nomor|nama>")
            return False
        m = find_model(rest)
        if not m:
            error_line(f"Model '{rest}' tidak ditemukan. Coba '/models' untuk daftar lengkap.")
            return False
        state.model = m
        state.effort = closest_supported_effort(m, state.effort)
        state.config["default_model_key"] = m["key"]
        save_config(state.config)
        success_line(f"Model aktif diganti ke: {m['label']} ({m['id']})")
        return False

    if name == "/think":
        arg = rest.lower().strip()
        if arg in ("on", "aktif", "nyala"):
            state.thinking_on = True
            state.config["thinking"] = True
            save_config(state.config)
            success_line("Thinking model: ON.")
        elif arg in ("off", "mati", "nonaktif"):
            state.thinking_on = False
            state.config["thinking"] = False
            save_config(state.config)
            success_line("Thinking model: OFF.")
        elif arg in ("show", "buka", "tampil", "lihat"):
            state.show_thinking = True
            state.config["show_thinking"] = True
            save_config(state.config)
            success_line("Blok thinking: DITAMPILKAN.")
        elif arg in ("hide", "tutup", "sembunyi"):
            state.show_thinking = False
            state.config["show_thinking"] = False
            save_config(state.config)
            success_line("Blok thinking: DISEMBUNYIKAN (tetap dihitung, /think show buat buka lagi).")
        elif arg in ("toggle",):
            state.show_thinking = not state.show_thinking
            state.config["show_thinking"] = state.show_thinking
            save_config(state.config)
            success_line(
                "Blok thinking: " + ("DITAMPILKAN." if state.show_thinking else "DISEMBUNYIKAN.")
            )
        else:
            status = []
            status.append(f"Reasoning model : {'ON' if state.thinking_on else 'OFF'}")
            status.append(
                f"Tampilan blok   : {'TAMPIL' if state.show_thinking else 'SEMBUNYI'}"
            )
            system_line("\n".join(status))
            system_line("Pakai: /think on|off   dan   /think show|hide|toggle")
        return False

    if name == "/effort":
        if not rest:
            system_line("Pakai: /effort <none|low|medium|high|xhigh|max>  (xhigh = extreme)")
            return False
        level = normalize_effort(rest)
        if not level:
            error_line(f"Level upaya '{rest}' tidak dikenal.")
            return False
        final_level = closest_supported_effort(state.model, level)
        if final_level != level:
            system_line(
                f"Model {state.model['label']} tidak dukung '{level}', dipetakan ke '{final_level}'.",
                FG_YELLOW,
            )
        state.effort = final_level
        state.config["default_effort"] = final_level
        save_config(state.config)
        success_line(f"Level upaya diatur ke: {final_level.upper()}")
        return False

    if name == "/limit":
        if not rest:
            system_line(f"Batas langkah sekarang: {state.max_steps} (pakai: /limit <n>)")
            return False
        try:
            n = max(1, min(200, int(rest)))
        except ValueError:
            error_line(f"'{rest}' bukan angka. Pakai: /limit <n>")
            return False
        state.max_steps = n
        state.config["max_steps"] = n
        save_config(state.config)
        success_line(f"Batas langkah per tugas: {n}")
        return False

    if name == "/search":
        arg = rest.lower().strip()
        cfg = state.config
        if not rest:
            arg = "show"
        if arg == "show":
            engine = cfg.get("search_engine", "auto")
            if engine == "auto":
                engine = "auto → SearXNG" if cfg.get("searxng_url") else "auto → DDG"
            system_line(
                f"engine      : {engine}\n"
                f"searxng_url : {cfg.get('searxng_url') or '(belum di-set)'}\n"
                f"pakai       : /search ddg | /search auto | /search searxng <url> | /search test <query>"
            )
            return False
        if arg == "ddg":
            cfg["search_engine"] = "ddg"
            save_config(cfg)
            success_line("Engine search: DuckDuckGo (tanpa API key).")
            return False
        if arg == "auto":
            cfg["search_engine"] = "auto"
            save_config(cfg)
            success_line("Engine search: auto (SearXNG kalau di-set, kalau tidak DDG).")
            return False
        if arg.startswith("searxng"):
            sub = arg[len("searxng"):].strip()
            if sub == "" or sub == "show":
                system_line(
                    f"SearXNG URL sekarang: {cfg.get('searxng_url') or '(belum di-set)'}\n"
                    f"Pakai: /search searxng https://searx.example.com   atau   /search searxng off"
                )
                return False
            if sub == "off":
                cfg["searxng_url"] = ""
                if cfg.get("search_engine") == "searxng":
                    cfg["search_engine"] = "auto"
                save_config(cfg)
                success_line("SearXNG dimatikan. Engine balik ke auto/DDG.")
                return False
            url = sub
            if not re.match(r"^https?://", url):
                error_line("URL SearXNG harus diawali http:// atau https://")
                return False
            cfg["searxng_url"] = url.rstrip("/")
            cfg["search_engine"] = "searxng"
            save_config(cfg)
            success_line(f"SearXNG di-set ke: {url}")
            return False
        if arg.startswith("test"):
            query = rest[len("test"):].strip()
            if not query:
                error_line("Pakai: /search test <query>")
                return False
            system_line(f"🔎 Mencari \"{query}\" (5 hasil)...", FG_YELLOW)
            try:
                results, used, note = web_search(state.config, query, 5)
            except Exception as e:
                error_line(f"Search gagal: {e}")
                return False
            header = f"{len(results)} hasil untuk \"{query}\" via {used.upper()}"
            if note:
                header += f"  [{note}]"
            if not results:
                system_line(header)
                return False
            _print_search_results(header + "\n\n" + "\n".join(
                f"{i}. {r['title']}\n   {r['url']}\n   {(r.get('snippet') or '')[:200]}"
                for i, r in enumerate(results, 1)
            ))
            return False
        error_line("Sub-perintah /search tidak dikenal. Ketik /search buat lihat opsi.")
        return False

    if name == "/fetch":
        if not rest:
            error_line("Pakai: /fetch <url>")
            return False
        system_line(f"📄 Fetching {rest} ...", FG_YELLOW)
        try:
            title, text = web_fetch(state.config, rest)
        except Exception as e:
            error_line(f"Fetch gagal: {e}")
            return False
        _print_search_results(f"[OK] {title} — {rest}\n{text}")
        return False

    if name == "/connect":
        if rest.lower() == "show":
            cfg = state.config
            masked_key = (
                (cfg["api_key"][:4] + "…" + cfg["api_key"][-4:])
                if cfg.get("api_key") and len(cfg["api_key"]) > 8
                else ("(kosong)" if not cfg.get("api_key") else "****")
            )
            system_line(
                f"provider   : {cfg.get('provider')}\n"
                f"base_url   : {cfg.get('base_url')}\n"
                f"auth_header: {cfg.get('auth_header')}\n"
                f"api_key    : {masked_key}\n"
                f"config file: {CONFIG_PATH}"
            )
            return False
        if rest.lower() == "test":
            ok, msg = test_connection(state.config)
            (success_line if ok else error_line)(msg)
            return False
        state.config = connect_wizard(state.config)
        return False

    error_line(f"Perintah '{name}' tidak dikenal. Ketik /help untuk daftar perintah.")
    return False


def connect_wizard(cfg):
    system_line("── /connect : setup koneksi API (template Xkiro.com) ──")
    system_line(
        "Base URL default sudah diarahkan ke gateway Xkiro (https://api.xkiro.com/v1)."
    )
    base_url = input(
        f"Base URL [{cfg.get('base_url') or DEFAULT_CONFIG['base_url']}]: "
    ).strip()
    if base_url:
        cfg["base_url"] = base_url
    elif not cfg.get("base_url"):
        cfg["base_url"] = DEFAULT_CONFIG["base_url"]

    header_choice = input(
        "Header auth: [1] Authorization: Bearer <key>  [2] x-api-key: <key>  (default 1): "
    ).strip()
    cfg["auth_header"] = "x-api-key" if header_choice == "2" else "Authorization"

    current = cfg.get("api_key", "")
    hint = f"(kosongkan buat pakai key lama: ...{current[-4:]})" if current else ""
    try:
        key = getpass.getpass(f"XKIRO API Key {hint}: ").strip()
    except Exception:
        key = input(f"XKIRO API Key {hint}: ").strip()
    if key:
        cfg["api_key"] = key
    elif not current:
        env_key = os.environ.get("XKIRO_API_KEY", "")
        if env_key:
            cfg["api_key"] = env_key
            system_line("Pakai XKIRO_API_KEY dari environment variable.")

    save_config(cfg)
    success_line(f"Konfigurasi tersimpan di {CONFIG_PATH}")
    if not cfg.get("api_key"):
        error_line(
            "API key masih kosong. Set lewat 'export XKIRO_API_KEY=...' atau ulangi /connect."
        )
    return cfg


# ============================================================================
# LOOP UTAMA AGENT: thinking -> (search) -> thinking -> hasil
# ============================================================================

def _print_workflow_receipt():
    """Struk disiplin kerja: skill apa yang dipakai + bukti verifikasinya."""
    wf = WORKFLOW
    s = wf.summary()
    if not any(s.values()):
        return
    w = term_width()
    print(f"{BG_DARKGREY}{FG_CYAN}{BOLD}{' 🦸 Superpowers — catatan kerja '.ljust(w)}{RESET}")
    if s["skills"]:
        print(f"   {FG_CYAN}Skill dipakai :{RESET} {', '.join(s['skills'])}")
    if s["approvals"]:
        print(f"   {FG_CYAN}Approval      :{RESET} {s['approvals']}x dari partner manusia")
    if s["todos"]:
        done = sum(1 for t in wf.todos if t.get("status") == "done")
        print(f"   {FG_CYAN}Rencana       :{RESET} {done}/{s['todos']} task beres")
    if s["files"]:
        print(f"   {FG_CYAN}File disentuh :{RESET} {s['files']}")
    if wf.verifications:
        print(f"   {FG_GREEN}Bukti verifikasi ({len(wf.verifications)}):{RESET}")
        for v in wf.verifications[-4:]:
            print(f"     {FG_GREEN}✔{RESET} {DIM}{v['cmd']}{RESET}")
    elif s["files"]:
        print(f"   {FG_YELLOW}⚠ Belum ada bukti verifikasi yang kejalan.{RESET}")
    print()


def _print_download_hint():
    if not LAST_TASK_FILES:
        return
    print(f"{BG_DARKGREY}{FG_GREEN}{BOLD} 📦 File hasil kerja (workspace/):{RESET}")
    for i, f in enumerate(LAST_TASK_FILES, 1):
        print(f"   {FG_GREEN}{BOLD}{i}.{RESET} {f}")
    if len(LAST_TASK_FILES) == 1:
        cmd = f"/download -f {LAST_TASK_FILES[0]}"
    else:
        cmd = "/download"
    print(
        f"{FG_GREEN}{BOLD}💾 Click here to download: {cmd}{RESET}  "
        f"{DIM}(zip otomatis ke folder downloads/){RESET}"
    )
    print()


def run_task(task, state):
    global LAST_TASK_FILES
    LAST_TASK_FILES = []
    WORKFLOW.reset()
    state.messages.append({"role": "user", "content": task})
    state.step_count = 0

    try:
        for _step in range(state.max_steps):
            state.step_count += 1
            streamed = {"shown": False, "words": 0}

            def on_stream(kind, text):
                if kind != "thinking":
                    return
                streamed["words"] += len(text.split())
                if state.show_thinking:
                    if not streamed["shown"]:
                        thinking_header("🧠 Thinking")
                        streamed["shown"] = True
                    thinking_chunk(text)

            try:
                reply = send_chat(
                    state.config,
                    state.model["id"],
                    [{"role": "system", "content": build_system_prompt(state.config)}] + state.messages,
                    state.effort,
                    state.thinking_on,
                    on_stream=on_stream,
                )
            except ApiError as e:
                if streamed["shown"]:
                    thinking_footer()
                error_line(str(e))
                return

            if streamed["shown"]:
                thinking_footer()

            state.messages.append({"role": "assistant", "content": reply["content"]})
            parsed = parse_response(reply["content"])
            thinks = parsed.get("thinks", [])

            # --- tampilkan thinking (model reasoning + THINK) -----------------
            model_thinking = (reply.get("thinking") or "").strip()
            hidden_words = 0
            if model_thinking:
                if state.show_thinking:
                    if not streamed["shown"]:
                        thinking_block(model_thinking, "🧠 Thinking")
                else:
                    hidden_words += len(model_thinking.split())
            if thinks:
                if state.show_thinking:
                    for t in thinks:
                        thinking_block(t, "🧠 Plan")
                else:
                    hidden_words += sum(len(t.split()) for t in thinks)
            if hidden_words and not state.show_thinking:
                system_line(
                    f"🧠 Thinking… ({hidden_words} kata, disembunyikan — /think show buat lihat)",
                    FG_MAGENTA,
                )

            if parsed["kind"] == "done":
                gate = pre_done_gate(WORKFLOW, state.config)
                if gate:
                    gate_line(gate)
                    state.messages.append({
                        "role": "user",
                        "content": f"OBSERVATION: 🛑 {gate}",
                    })
                    continue
                done_line(parsed["summary"])
                _print_workflow_receipt()
                _print_download_hint()
                return

            if parsed["kind"] == "error":
                observation = (
                    f"OBSERVATION: [Error] {parsed['error']} — "
                    f"ikutin format THINK/ACTION/INPUT atau DONE."
                )
                error_line(parsed["error"])
            else:
                tool_name, args = parsed["tool"], parsed["args"]

                # --- GATE: disiplin Superpowers sebelum aksi dieksekusi ------
                gate = pre_action_gate(tool_name, args, WORKFLOW, state.config)
                if gate:
                    action_line(tool_name, args)
                    gate_line(gate)
                    state.messages.append({
                        "role": "user",
                        "content": f"OBSERVATION: 🛑 {gate}",
                    })
                    continue

                action_line(tool_name, args)
                if tool_name not in TOOLS:
                    result = f"[Error] Tool '{tool_name}' tidak dikenal."
                    observation = f"OBSERVATION: {result}"
                else:
                    try:
                        result = TOOLS[tool_name](args, state.config)
                    except Exception as e:
                        result = f"[Error {tool_name}: {e}]"
                    workflow_record(tool_name, args, result, WORKFLOW, state.step_count)
                    observation = f"OBSERVATION: {result}"
                if tool_name == "web_search":
                    _print_search_results(result)
                elif tool_name in ("todo_write", "ask_user"):
                    pass  # sudah punya panel sendiri
                else:
                    observation_line(observation, tool_name=tool_name)

            state.messages.append({"role": "user", "content": observation})

        error_line(f"Melebihi batas langkah maksimum ({state.max_steps}) untuk tugas ini.")

    except KeyboardInterrupt:
        system_line("⏹ Tugas dibatalkan.", FG_YELLOW)
        if state.messages and state.messages[-1]["role"] == "user":
            state.messages.pop()


def _find_real_agent_dir(start):
    """Cari folder Agent asli (yang ada main.py-nya) di sekitar `start`.

    Kasus paling sering di Termux: user kejebak di ~/Agent/Agent yang KOSONG
    gara-gara clone gagal / keinterupsi, terus bingung kenapa main.py gak ada.
    """
    start = os.path.abspath(start)
    cands = []
    # naik ke atas: ~/Agent/Agent -> ~/Agent -> ~
    cur = start
    for _ in range(4):
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cands.append(parent)
        cur = parent
    # turun ke bawah 1 level
    try:
        for name in sorted(os.listdir(start)):
            p = os.path.join(start, name)
            if os.path.isdir(p):
                cands.append(p)
    except OSError:
        pass
    for c in cands:
        if os.path.isfile(os.path.join(c, "main.py")) and os.path.isdir(
            os.path.join(c, "skills")
        ):
            return c
    return None


def doctor(verbose=True):
    """Cek instalasi sehat apa enggak. Return True kalau aman.

    Ini yang nolongin user Termux yang kejebak 'Agent/Agent kosong'.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    problems = []
    n_skills = len(load_skills())

    if not os.path.isdir(SKILLS_DIR):
        problems.append(
            "Folder skills/ GAK ADA — Superpowers mati, agent jalan mode polos."
        )
    elif n_skills == 0:
        problems.append("Folder skills/ ada tapi KOSONG — gak ada skill yang kemuat.")

    try:
        import requests  # noqa: F401
    except ImportError:
        problems.append("Modul 'requests' belum keinstall — jalanin: pip install -r requirements.txt")

    if sys.version_info < (3, 7):
        problems.append(
            f"Python kamu {sys.version_info.major}.{sys.version_info.minor} — butuh minimal 3.7."
        )

    if not verbose:
        return not problems

    w = term_width()
    print(f"{FG_CYAN}{BOLD}{'═' * w}{RESET}")
    print(f"{FG_CYAN}{BOLD}🩺 Agent Doctor — cek instalasi{RESET}")
    print(f"{FG_CYAN}{BOLD}{'═' * w}{RESET}")
    print(f"  Versi Agent   : v{VERSION}")
    print(f"  Python        : {sys.version.split()[0]}  ({sys.executable})")
    print(f"  Lokasi main.py: {os.path.join(here, 'main.py')}")
    print(f"  Folder kerja  : {os.getcwd()}")
    print(f"  Folder skills : {SKILLS_DIR}")
    print(f"  Skill kemuat  : {n_skills}")
    print(f"  Lebar layar   : {w} kolom{'  (mode HP/sempit)' if is_narrow() else ''}")
    print()

    if problems:
        for p in problems:
            error_line(p)
        print()
        system_line("Cara benerin (copy-paste aja):", FG_YELLOW)
        print(f"{FG_YELLOW}  cd ~{RESET}")
        print(f"{FG_YELLOW}  rm -rf Agent{RESET}")
        print(f"{FG_YELLOW}  git clone https://github.com/EdwardsVD/Agent.git{RESET}")
        print(f"{FG_YELLOW}  cd Agent{RESET}")
        print(f"{FG_YELLOW}  pip install -r requirements.txt{RESET}")
        print(f"{FG_YELLOW}  python main.py{RESET}")
        print()
        return False

    success_line("Semua aman. Superpowers siap dipakai.")
    print()
    return True


def _bootstrap_check():
    """Dipanggil paling awal. Kalau user kejebak folder kosong, kasih tau
    JALAN KELUARNYA — bukan cuma error Python yang bikin bingung."""
    here = os.path.dirname(os.path.abspath(__file__))
    if os.path.isdir(os.path.join(here, "skills")):
        return
    real = _find_real_agent_dir(os.getcwd())
    if real and os.path.abspath(real) != os.path.abspath(here):
        print()
        error_line("Kayaknya kamu jalanin dari folder yang salah.")
        system_line(f"  Folder Agent yang bener ada di: {real}", FG_YELLOW)
        system_line("  Coba jalanin ini:", FG_YELLOW)
        print(f"{FG_GREEN}{BOLD}    cd {real} && python main.py{RESET}")
        print()


def main():
    argv = sys.argv[1:]
    if "--version" in argv or "-V" in argv:
        print(f"Agent CLI v{VERSION}")
        return
    if "--help" in argv or "-h" in argv:
        print(f"Agent CLI v{VERSION} — coding agent dengan Superpowers\n")
        print("Cara pakai:  python main.py [opsi]\n")
        print("Opsi:")
        print("  --no-anim     Lewati animasi pembuka (lebih cepat di HP)")
        print("  --doctor      Cek instalasi sehat apa enggak, lalu keluar")
        print("  --version     Tampilkan versi")
        print("  --help        Tampilkan bantuan ini")
        print("\nDi dalam program, ketik /help buat daftar perintah lengkap.")
        return
    if os.name == "nt":
        os.system("")  # aktifkan ANSI di cmd Windows
    if "--doctor" in argv:
        sys.exit(0 if doctor() else 1)
    _bootstrap_check()
    state = State()
    intro_animation()
    banner()
    toolbar(state)
    if not state.config.get("api_key"):
        system_line(
            "Belum ada API key tersambung. Ketik '/connect' dulu buat setup Xkiro.com.",
            FG_YELLOW,
        )
    print()

    while True:
        try:
            raw = input(f"{BOLD}You ›{RESET} ")
        except (EOFError, KeyboardInterrupt):
            print()
            system_line("Sampai jumpa!", FG_CYAN)
            break

        text = raw.strip()
        if not text:
            continue

        if text.startswith("/"):
            should_exit = handle_slash_command(text, state)
            print()
            toolbar(state)
            if should_exit:
                break
            continue

        if text.startswith("!"):
            cmd = text[1:].strip()
            if not cmd:
                continue
            system_line(f"💻 bash › {cmd}", FG_YELLOW)
            result = tool_bash({"command": cmd, "timeout": 120}, state.config)
            observation_line(result)
            toolbar(state)
            continue

        user_bubble(text)
        run_task(text, state)
        toolbar(state)


if __name__ == "__main__":
    main()
