"""
api_client.py
-------------
Klien HTTP buat manggil model lewat gateway Xkiro.com, pakai dialek
OpenAI Chat Completions (POST {base_url}/chat/completions) karena
paling universal buat semua vendor (Anthropic/OpenAI/Qwen/Kimi) yang
dipetakan Xkiro lewat satu API key.

Parameter "reasoning" dipakai buat kontrol on/off + level upaya (effort)
thinking model, mengikuti pola umum gateway reasoning-capable models:
    - thinking OFF -> {"reasoning": {"enabled": false}}
    - thinking ON  -> {"reasoning": {"effort": "<low|medium|high|xhigh|max>"}}
"""

import requests

from config import build_auth_headers


class ApiError(Exception):
    pass


def send_chat(cfg, model_id, messages, effort, thinking_on, max_tokens=1024, timeout=90):
    if not cfg.get("api_key"):
        raise ApiError("Belum ada API key. Jalankan '/connect' dulu.")

    base_url = (cfg.get("base_url") or "https://api.xkiro.com/v1").rstrip("/")
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

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    except requests.RequestException as e:
        raise ApiError(f"Gagal konek ke {url}: {e}")

    if resp.status_code != 200:
        raise ApiError(f"HTTP {resp.status_code} dari Xkiro: {resp.text[:500]}")

    try:
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        raise ApiError(f"Format respons tidak dikenali: {e} — raw: {resp.text[:500]}")


def test_connection(cfg, timeout=15):
    """Dipakai oleh '/connect test' buat ngecek base_url + api key valid (GET /models)."""
    if not cfg.get("api_key"):
        return False, "API key kosong."
    base_url = (cfg.get("base_url") or "https://api.xkiro.com/v1").rstrip("/")
    url = f"{base_url}/models"
    headers = build_auth_headers(cfg)
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
    except requests.RequestException as e:
        return False, f"Gagal konek: {e}"
    if resp.status_code == 200:
        return True, "Koneksi OK."
    return False, f"HTTP {resp.status_code}: {resp.text[:300]}"
