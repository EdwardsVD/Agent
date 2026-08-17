"""
config.py
---------
Template koneksi ke API (khusus disiapkan untuk Xkiro.com, gateway "satu API
buat banyak model": https://docs.xkiro.com/).

Xkiro kompatibel dengan format OpenAI Chat Completions (POST /v1/chat/completions)
maupun Anthropic Messages (POST /v1/messages). Di sini kita pakai dialek OpenAI
karena paling universal buat semua vendor model yang dipetakan Xkiro.

Konfigurasi disimpan di ~/.opencode_clone/connect.json supaya persist antar sesi.
API key BOLEH juga diisi lewat environment variable XKIRO_API_KEY (lebih aman,
gak ke-commit ke file config).
"""

import os
import json
import getpass

CONFIG_DIR = os.path.expanduser("~/.opencode_clone")
CONFIG_PATH = os.path.join(CONFIG_DIR, "connect.json")

# ==== TEMPLATE default buat provider Xkiro.com ====
DEFAULT_CONFIG = {
    "provider": "xkiro",
    "base_url": "https://api.xkiro.com/v1",   # base URL resmi Xkiro
    "auth_header": "Authorization",           # bisa juga pakai header "x-api-key"
    "api_key": "",                            # diisi lewat /connect atau env XKIRO_API_KEY
    "default_model_key": "sonnet46",
    "default_effort": "medium",
    "thinking": True,
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
            cfg.update(saved)
        except Exception:
            pass

    # Env var selalu bisa nimpa/isi api_key kalau file config kosong
    env_key = os.environ.get("XKIRO_API_KEY", "")
    if env_key and not cfg.get("api_key"):
        cfg["api_key"] = env_key

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


def connect_wizard(cfg, ui):
    """Wizard interaktif untuk perintah /connect — isi base_url + api key provider Xkiro.com."""
    ui.system_line("── /connect : setup koneksi API (template Xkiro.com) ──")
    ui.system_line(
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
            ui.system_line("Pakai XKIRO_API_KEY dari environment variable.")

    save_config(cfg)
    ui.success_line(f"Konfigurasi tersimpan di {CONFIG_PATH}")
    if not cfg.get("api_key"):
        ui.error_line(
            "API key masih kosong. Set lewat 'export XKIRO_API_KEY=...' atau ulangi /connect."
        )
    return cfg


def build_auth_headers(cfg):
    key = cfg.get("api_key", "")
    if cfg.get("auth_header") == "x-api-key":
        return {"x-api-key": key}
    return {"Authorization": f"Bearer {key}"}
