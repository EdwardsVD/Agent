"""
ui.py
-----
Semua urusan tampilan terminal: warna ANSI, toolbar status, dan "bubble"
chat (user dikasih background biru, agent & tool warna beda biar gampang dibedain).
Murni pakai kode ANSI standar (tanpa dependency tambahan) supaya tetap "py only".
"""

import shutil
import textwrap

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

FG_WHITE = "\033[97m"
FG_BLACK = "\033[30m"
FG_GREEN = "\033[92m"
FG_YELLOW = "\033[93m"
FG_CYAN = "\033[96m"
FG_RED = "\033[91m"
FG_GREY = "\033[37m"

BG_BLUE = "\033[44m"
BG_DARKGREY = "\033[100m"
BG_GREEN = "\033[42m"


def term_width(default=78):
    try:
        return max(50, min(100, shutil.get_terminal_size().columns))
    except Exception:
        return default


def _wrap_lines(text, width):
    lines = []
    for raw_line in text.splitlines() or [""]:
        wrapped = textwrap.wrap(
            raw_line, width=width, break_long_words=True, break_on_hyphens=False
        ) or [""]
        lines.extend(wrapped)
    return lines


def banner():
    w = term_width()
    title = "opencode-clone  ·  agent CLI Python (Xkiro.com ready)"
    line = "═" * w
    print(f"{FG_CYAN}{BOLD}{line}{RESET}")
    print(f"{FG_CYAN}{BOLD}{title.center(w)}{RESET}")
    print(f"{FG_CYAN}{BOLD}{line}{RESET}")
    print(
        f"{DIM}Ketik pesan biasa untuk kasih tugas ke agent, atau pakai perintah "
        f"'/help' untuk lihat semua slash-command (mis. /connect, /model, /think, /effort).{RESET}\n"
    )


def toolbar(state):
    """Status bar tipis yang nunjukin model aktif, level upaya, status thinking, dan koneksi API."""
    w = term_width()
    model = state.model
    effort_display = "OFF" if not state.thinking_on else state.effort.upper()
    conn = state.config.get("api_key", "")
    if conn:
        masked = conn[:4] + "…" + conn[-4:] if len(conn) > 8 else "*" * len(conn)
        conn_text = f"connected ({masked})"
        conn_color = FG_GREEN
    else:
        conn_text = "belum /connect"
        conn_color = FG_RED

    left = f" Model: {model['label']} ({model['id']}) "
    mid = f" Upaya: {effort_display} "
    right = f" Endpoint: {state.config.get('base_url', '-')} "

    line1 = f"{BG_DARKGREY}{FG_WHITE}{BOLD}{left}{RESET}{BG_DARKGREY}{FG_YELLOW}{mid}{RESET}"
    line1 = line1 + f"{BG_DARKGREY}{FG_CYAN}{right}{RESET}"
    pad = max(0, w - _visible_len(line1))
    line1 = line1 + f"{BG_DARKGREY}{' ' * pad}{RESET}"

    line2_text = f" Status: {conn_text} "
    line2 = f"{BG_DARKGREY}{conn_color}{BOLD}{line2_text}{RESET}"
    pad2 = max(0, w - _visible_len(line2))
    line2 = line2 + f"{BG_DARKGREY}{' ' * pad2}{RESET}"

    print(line1)
    print(line2)


def _visible_len(s: str) -> int:
    """Hitung panjang string tanpa menghitung kode ANSI escape."""
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


def user_bubble(text):
    """Pesan user ditampilkan dengan background biru, sesuai permintaan."""
    w = term_width()
    inner_w = w - 4
    print()
    print(f"{BG_BLUE}{FG_WHITE}{BOLD}{' You'.ljust(w)}{RESET}")
    for line in _wrap_lines(text, inner_w):
        content = f"  {line}"
        pad = " " * max(0, w - len(content))
        print(f"{BG_BLUE}{FG_WHITE}{content}{pad}{RESET}")
    print()


def agent_bubble(text, label="Agent"):
    w = term_width()
    print(f"{FG_GREEN}{BOLD}{label}{RESET}")
    for line in _wrap_lines(text, w):
        print(f"{FG_GREEN}{line}{RESET}")
    print()


def action_line(tool_name, args):
    print(f"{FG_YELLOW}{BOLD}⚙ ACTION{RESET} {FG_YELLOW}{tool_name}{RESET} {DIM}{args}{RESET}")


def observation_line(text):
    w = term_width()
    for line in _wrap_lines(text, w):
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
