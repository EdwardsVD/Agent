"""
opencode-clone (versi sederhana) — enhanced edition
----------------------------------------------------
AI cuma boleh balas dalam format yang ketat, gak ada tebak-tebakan.
Tool yang tersedia: read_file, write_file, edit_file, bash.

Tambahan di versi ini:
    - Toolbar status (model aktif, level upaya, status thinking, status koneksi)
    - Chat user ditampilkan dengan background BIRU
    - Slash-command: /connect, /model, /think, /effort, /help, /clear, /status, /exit
    - Template koneksi API siap pakai untuk Xkiro.com (banyak model, 1 API key)
    - Daftar model lengkap: Fable 5, Opus 5, Sonnet 5, Sonnet 4.6, Opus 4.6,
      GPT-5.6 Sol/Terra/Luna, Qwen3.8 Max, Kimi K3
    - Thinking bisa di-ON/OFF, dan level upaya (effort) low/medium/high/xhigh/max

Cara pakai:
    cd python-agent
    pip install -r requirements.txt
    export XKIRO_API_KEY="..."     # opsional, bisa juga diisi lewat /connect
    python agent.py
"""

import re
import json

import ui
import config as cfgmod
from models import (
    MODEL_CATALOG,
    DEFAULT_MODEL_KEY,
    find_model,
    get_model_by_key,
    normalize_effort,
    closest_supported_effort,
)
from tools import TOOLS
from api_client import send_chat, test_connection, ApiError

SYSTEM_PROMPT = """Kamu adalah coding agent sederhana. Kamu HANYA boleh balas dengan salah satu format berikut, PERSIS, tanpa teks lain di luar format:

Untuk pakai tool:
ACTION: <nama_tool>
INPUT: <json satu baris>

Tool yang tersedia:
- read_file {"path": "..."}
- write_file {"path": "...", "content": "..."}
- edit_file {"path": "...", "old": "...", "new": "..."}
- bash {"command": "..."}

Kalau tugas sudah selesai:
DONE: <ringkasan singkat apa yang sudah dilakukan>

Jangan pernah menebak isi file — selalu read_file dulu sebelum edit_file.
"""

ACTION_RE = re.compile(r"ACTION:\s*(\w+)\s*\nINPUT:\s*(\{.*\})", re.DOTALL)
DONE_RE = re.compile(r"DONE:\s*(.*)", re.DOTALL)

HELP_TEXT = """Perintah yang tersedia:
  /connect            Setup / cek koneksi API (template Xkiro.com)
  /connect test       Tes koneksi API pakai konfigurasi saat ini
  /connect show       Tampilkan konfigurasi koneksi saat ini
  /models             Lihat semua model yang tersedia
  /model <no|nama>    Ganti model aktif, contoh: /model kimik3  atau  /model 7
  /think on|off       Nyalakan / matikan thinking (reasoning) model
  /effort <level>     Atur level upaya: none,low,medium,high,xhigh(extreme),max
  /status             Tampilkan toolbar status sekarang
  /clear              Kosongkan riwayat percakapan
  /help               Tampilkan bantuan ini
  /exit atau /quit    Keluar dari program

Selain itu, ketik pesan biasa untuk kasih tugas ke coding agent."""


class State:
    def __init__(self):
        self.config = cfgmod.load_config()
        self.model = get_model_by_key(self.config.get("default_model_key", DEFAULT_MODEL_KEY))
        self.thinking_on = bool(self.config.get("thinking", True))
        self.effort = closest_supported_effort(
            self.model, self.config.get("default_effort", self.model["default_effort"])
        )
        self.messages = []  # riwayat percakapan role/content, dikirim ke model


def print_models():
    ui.system_line("Model yang tersedia lewat Xkiro.com:", ui.FG_CYAN)
    for i, m in enumerate(MODEL_CATALOG, start=1):
        efforts = ", ".join(m["efforts"])
        print(
            f"  {ui.BOLD}{i:>2}.{ui.RESET} {m['label']:<18} "
            f"{ui.DIM}({m['id']}){ui.RESET}  {ui.FG_YELLOW}upaya: {efforts}{ui.RESET}"
        )
    print()


def handle_slash_command(cmd: str, state: State) -> bool:
    """Return True kalau program harus berhenti."""
    parts = cmd.strip().split(maxsplit=1)
    name = parts[0].lower()
    rest = parts[1].strip() if len(parts) > 1 else ""

    if name in ("/exit", "/quit"):
        ui.system_line("Sampai jumpa!", ui.FG_CYAN)
        return True

    if name == "/help":
        ui.system_line(HELP_TEXT)
        return False

    if name == "/status":
        ui.toolbar(state)
        return False

    if name == "/clear":
        state.messages = []
        ui.success_line("Riwayat percakapan dikosongkan.")
        return False

    if name == "/models":
        print_models()
        return False

    if name == "/model":
        if not rest:
            print_models()
            ui.system_line("Pakai: /model <nomor|nama>")
            return False
        m = find_model(rest)
        if not m:
            ui.error_line(f"Model '{rest}' tidak ditemukan. Coba '/models' untuk daftar lengkap.")
            return False
        state.model = m
        state.effort = closest_supported_effort(m, state.effort)
        state.config["default_model_key"] = m["key"]
        cfgmod.save_config(state.config)
        ui.success_line(f"Model aktif diganti ke: {m['label']} ({m['id']})")
        return False

    if name == "/think":
        if rest.lower() in ("on", "aktif", "nyala"):
            state.thinking_on = True
            state.config["thinking"] = True
            cfgmod.save_config(state.config)
            ui.success_line("Thinking diaktifkan (ON).")
        elif rest.lower() in ("off", "mati", "nonaktif"):
            state.thinking_on = False
            state.config["thinking"] = False
            cfgmod.save_config(state.config)
            ui.success_line("Thinking dimatikan (OFF).")
        else:
            ui.system_line("Pakai: /think on   atau   /think off")
        return False

    if name == "/effort":
        if not rest:
            ui.system_line(
                "Pakai: /effort <none|low|medium|high|xhigh|max>  (xhigh = extreme)"
            )
            return False
        level = normalize_effort(rest)
        if not level:
            ui.error_line(f"Level upaya '{rest}' tidak dikenal.")
            return False
        final_level = closest_supported_effort(state.model, level)
        if final_level != level:
            ui.system_line(
                f"Model {state.model['label']} tidak dukung '{level}', dipetakan ke '{final_level}'.",
                ui.FG_YELLOW,
            )
        state.effort = final_level
        state.config["default_effort"] = final_level
        cfgmod.save_config(state.config)
        ui.success_line(f"Level upaya diatur ke: {final_level.upper()}")
        return False

    if name == "/connect":
        if rest.lower() == "show":
            cfg = state.config
            masked_key = (
                (cfg["api_key"][:4] + "…" + cfg["api_key"][-4:])
                if cfg.get("api_key") and len(cfg["api_key"]) > 8
                else ("(kosong)" if not cfg.get("api_key") else "****")
            )
            ui.system_line(
                f"provider   : {cfg.get('provider')}\n"
                f"base_url   : {cfg.get('base_url')}\n"
                f"auth_header: {cfg.get('auth_header')}\n"
                f"api_key    : {masked_key}\n"
                f"config file: {cfgmod.CONFIG_PATH}"
            )
            return False
        if rest.lower() == "test":
            ok, msg = test_connection(state.config)
            (ui.success_line if ok else ui.error_line)(msg)
            return False
        state.config = cfgmod.connect_wizard(state.config, ui)
        return False

    ui.error_line(f"Perintah '{name}' tidak dikenal. Ketik /help untuk daftar perintah.")
    return False


def parse_response(text: str):
    done_match = DONE_RE.search(text)
    if done_match:
        return ("done", done_match.group(1).strip())

    action_match = ACTION_RE.search(text)
    if action_match:
        tool_name = action_match.group(1).strip()
        try:
            args = json.loads(action_match.group(2))
        except json.JSONDecodeError:
            return ("error", "Format INPUT bukan JSON valid")
        return ("action", (tool_name, args))

    return ("error", "AI tidak mengikuti format yang diminta")


def run_task(task: str, state: State, max_steps: int = 15):
    state.messages.append({"role": "user", "content": task})

    for _ in range(max_steps):
        try:
            reply = send_chat(
                state.config,
                state.model["id"],
                [{"role": "system", "content": SYSTEM_PROMPT}] + state.messages,
                state.effort,
                state.thinking_on,
            )
        except ApiError as e:
            ui.error_line(str(e))
            return

        state.messages.append({"role": "assistant", "content": reply})
        kind, payload = parse_response(reply)

        if kind == "done":
            ui.done_line(payload)
            return

        if kind == "error":
            observation = f"OBSERVATION: [Error] {payload} — ikuti format ACTION/INPUT atau DONE."
            ui.error_line(payload)
        else:
            tool_name, args = payload
            ui.action_line(tool_name, args)
            if tool_name not in TOOLS:
                observation = f"OBSERVATION: [Error] Tool '{tool_name}' tidak dikenal."
            else:
                result = TOOLS[tool_name](args)
                observation = f"OBSERVATION: {result}"
            ui.observation_line(observation)

        state.messages.append({"role": "user", "content": observation})

    ui.error_line("Melebihi batas langkah maksimum untuk tugas ini.")


def main():
    state = State()
    ui.banner()
    ui.toolbar(state)
    if not state.config.get("api_key"):
        ui.system_line(
            "Belum ada API key tersambung. Ketik '/connect' dulu untuk setup Xkiro.com.",
            ui.FG_YELLOW,
        )
    print()

    while True:
        try:
            raw = input(f"{ui.BOLD}You ›{ui.RESET} ")
        except (EOFError, KeyboardInterrupt):
            print()
            ui.system_line("Sampai jumpa!", ui.FG_CYAN)
            break

        text = raw.strip()
        if not text:
            continue

        if text.startswith("/"):
            should_exit = handle_slash_command(text, state)
            print()
            ui.toolbar(state)
            if should_exit:
                break
            continue

        ui.user_bubble(text)
        run_task(text, state)
        ui.toolbar(state)


if __name__ == "__main__":
    main()
