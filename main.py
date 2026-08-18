#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent CLI — coding agent 1 file Python (thinking + AI search)
==============================================================
Update dari opencode-clone. Semua fitur digabung jadi SATU file biar gampang:

    git clone https://github.com/EdwardsVD/Agent.git
    cd Agent
    pip install -r requirements.txt
    python3 main.py

Fitur baru:
    - Thinking model DIPERLIHATKAN jelas, bisa dibuka/tutup: /think show|hide
      (alur: THINK -> cari di web -> THINK lagi -> hasil akhir)
    - AI search built-in lewat DuckDuckGo (tanpa API key) DAN SearXNG
      (instance sendiri, bisa di-set lewat /search searxng <url> atau env SEARXNG_URL)
    - Tool baru untuk model: web_search + web_fetch, plus read/write/edit/bash
    - Streaming respons (fallback otomatis ke non-stream kalau provider nolak)
    - Edit file pake pencocokan fuzzy (gak strict soal spasi/indentasi)
    - Jawaban lebih akurat: model diminta cari sumber & cantumkan [1](url) di jawaban

Koneksi API: template Xkiro.com (OpenAI-compatible). API key lewat /connect
atau env XKIRO_API_KEY. Konfigurasi tersimpan di ~/.opencode_clone/connect.json
"""

import os
import re
import sys
import json
import time
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

VERSION = "2.0.0"

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
    "max_steps": 30,                      # maks. langkah agent per tugas
    "stream": True,                       # streaming (fallback otomatis)
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
FG_YELLOW = "\033[93m"
FG_CYAN = "\033[96m"
FG_RED = "\033[91m"
FG_GREY = "\033[37m"
FG_MAGENTA = "\033[95m"

BG_BLUE = "\033[44m"
BG_DARKGREY = "\033[100m"
BG_GREEN = "\033[42m"


def term_width(default=78):
    try:
        return max(50, min(100, shutil.get_terminal_size().columns))
    except Exception:
        return default


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


def banner():
    w = term_width()
    title = f"Agent CLI v{VERSION}  ·  thinking + AI search (DDG / SearXNG)"
    line = "═" * w
    print(f"{FG_CYAN}{BOLD}{line}{RESET}")
    print(f"{FG_CYAN}{BOLD}{title.center(w)}{RESET}")
    print(f"{FG_CYAN}{BOLD}{line}{RESET}")
    print(
        f"{DIM}Ketik tugas biasa buat agent (agent bisa web_search/web_fetch kalau butuh), "
        f"atau '/help' buat daftar perintah.{RESET}\n"
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

    line2_text = f" Status: {conn_text} "
    line2 = f"{BG_DARKGREY}{conn_color}{BOLD}{line2_text}{RESET}"
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


def web_fetch(cfg, url, max_chars=3500):
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


def _safe_path(path):
    full = os.path.abspath(os.path.join(WORKSPACE_DIR, path))
    if not full.startswith(WORKSPACE_DIR):
        raise ValueError("Akses di luar workspace ditolak")
    return full


def tool_read_file(args, cfg):
    try:
        with open(_safe_path(args["path"]), "r") as f:
            content = f.read()
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
        return f"[OK] File diedit: {args['path']}"
    except Exception as e:
        return f"[Error edit_file: {e}]"


def tool_bash(args, cfg):
    try:
        result = subprocess.run(
            args["command"],
            shell=True,
            cwd=WORKSPACE_DIR,
            capture_output=True,
            text=True,
            timeout=int(args.get("timeout", 30)),
        )
        out = (result.stdout + result.stderr).strip()
        return out or "[Tidak ada output]"
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


TOOLS = {
    "read_file": tool_read_file,
    "write_file": tool_write_file,
    "edit_file": tool_edit_file,
    "bash": tool_bash,
    "web_search": tool_web_search,
    "web_fetch": tool_web_fetch,
}


# ============================================================================
# AGENT: prompt sistem, parser respons, loop THINK -> ACTION -> OBSERVATION
# ============================================================================

SYSTEM_PROMPT = """Kamu adalah coding agent CLI yang bekerja di sebuah workspace lokal. Kamu punya tool buat baca/tulis file, jalankan bash, DAN cari info di web (DuckDuckGo / SearXNG) supaya jawabanmu selalu akurat & terkini.

ATURAN RESPONS — balas HANYA dengan pola berikut, tanpa teks lain di luar pola:

THINK: <ringkasan singkat rencanamu, 1-3 kalimat>     (opsional)

ACTION: <nama_tool>
INPUT: <json satu baris>

atau kalau tugas sudah selesai:

DONE: <jawaban / ringkasan final>

TOOL YANG TERSEDIA:
- read_file  {"path": "..."}
- write_file {"path": "...", "content": "..."}
- edit_file  {"path": "...", "old": "...", "new": "..."}
- bash       {"command": "..."}
- web_search {"query": "...", "limit": 5, "engine": "auto|ddg|searxng"}
- web_fetch  {"url": "https://..."}

ALUR KERJA (penting):
1. THINK dulu: putuskan apakah tugas butuh info dari web (mis. dokumentasi library, versi terbaru, fakta yang bisa berubah, atau hal yang kamu ragu). Kalau iya -> web_search.
2. Baca hasil pencarian (OBSERVATION), lalu THINK lagi: kalau butuh detail, web_fetch halaman yang paling relevan.
3. Ulangi sampai yakin, lalu jawab dengan DONE.
4. Dalam DONE, cantumkan sumber sebagai [1](url), [2](url) kalau kamu pakai info dari web.
5. JANGAN menebak isi file: selalu read_file dulu sebelum edit_file/write_file.
6. JSON INPUT boleh multi-baris tapi harus valid JSON (pakai \\n untuk newline di dalam string).
7. Jawab pakai bahasa yang dipakai user (default Indonesia)."""


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
  /limit <n>                     Maks. langkah agent per tugas (default 30)
  /status                        Tampilkan toolbar status
  /clear                         Kosongkan riwayat percakapan
  /exit atau /quit               Keluar dari program

Selain itu, ketik pesan biasa untuk kasih tugas ke agent. Agent akan berpikir,
mencari di web kalau perlu (web_search / web_fetch), berpikir lagi, lalu menjawab."""


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


def handle_slash_command(cmd, state):
    """Return True kalau program harus berhenti."""
    parts = cmd.strip().split(maxsplit=1)
    name = parts[0].lower()
    rest = parts[1].strip() if len(parts) > 1 else ""

    if name in ("/exit", "/quit"):
        system_line("Sampai jumpa!", FG_CYAN)
        return True

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

def run_task(task, state):
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
                    [{"role": "system", "content": SYSTEM_PROMPT}] + state.messages,
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
                done_line(parsed["summary"])
                return

            if parsed["kind"] == "error":
                observation = (
                    f"OBSERVATION: [Error] {parsed['error']} — "
                    f"ikutin format THINK/ACTION/INPUT atau DONE."
                )
                error_line(parsed["error"])
            else:
                tool_name, args = parsed["tool"], parsed["args"]
                action_line(tool_name, args)
                if tool_name not in TOOLS:
                    observation = f"OBSERVATION: [Error] Tool '{tool_name}' tidak dikenal."
                else:
                    try:
                        result = TOOLS[tool_name](args, state.config)
                    except Exception as e:
                        result = f"[Error {tool_name}: {e}]"
                    observation = f"OBSERVATION: {result}"
                if tool_name == "web_search":
                    _print_search_results(result)
                else:
                    observation_line(observation, tool_name=tool_name)

            state.messages.append({"role": "user", "content": observation})

        error_line(f"Melebihi batas langkah maksimum ({state.max_steps}) untuk tugas ini.")

    except KeyboardInterrupt:
        system_line("⏹ Tugas dibatalkan.", FG_YELLOW)
        if state.messages and state.messages[-1]["role"] == "user":
            state.messages.pop()


def main():
    if os.name == "nt":
        os.system("")  # aktifkan ANSI di cmd Windows
    state = State()
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

        user_bubble(text)
        run_task(text, state)
        toolbar(state)


if __name__ == "__main__":
    main()
