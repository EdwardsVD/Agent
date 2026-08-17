"""
models.py
---------
Katalog model yang tersedia lewat gateway Xkiro.com (https://api.xkiro.com/v1).
Xkiro pakai format model ID "vendor/model" dan kompatibel dengan
OpenAI Chat Completions maupun Anthropic Messages.

Setiap model juga punya daftar level "upaya" (reasoning effort) yang didukung.
"none"  -> thinking dimatikan total (kalau model support)
"low/medium/high/xhigh/max" -> makin ke kanan makin dalam mikirnya (makin lambat/mahal)
"xhigh" sering juga disebut "extreme" di command /effort.
"""

# alias biar user bisa ketik macem-macem tapi tetep kepetakan ke level asli
EFFORT_ALIASES = {
    "none": "none",
    "off": "none",
    "nol": "none",
    "low": "low",
    "rendah": "low",
    "med": "medium",
    "medium": "medium",
    "sedang": "medium",
    "high": "high",
    "tinggi": "high",
    "xhigh": "xhigh",
    "extreme": "xhigh",
    "extrem": "xhigh",
    "ekstrem": "xhigh",
    "max": "max",
    "maks": "max",
    "maksimal": "max",
}

EFFORT_ORDER = ["none", "low", "medium", "high", "xhigh", "max"]

MODEL_CATALOG = [
    {
        "key": "fable5",
        "label": "Claude Fable 5",
        "id": "anthropic/claude-fable-5",
        "vendor": "Anthropic",
        "efforts": ["low", "medium", "high", "xhigh", "max"],
        "default_effort": "high",
    },
    {
        "key": "opus5",
        "label": "Claude Opus 5",
        "id": "anthropic/claude-opus-5",
        "vendor": "Anthropic",
        "efforts": ["low", "medium", "high", "xhigh", "max"],
        "default_effort": "high",
    },
    {
        "key": "sonnet5",
        "label": "Claude Sonnet 5",
        "id": "anthropic/claude-sonnet-5",
        "vendor": "Anthropic",
        "efforts": ["low", "medium", "high", "xhigh", "max"],
        "default_effort": "medium",
    },
    {
        "key": "sonnet46",
        "label": "Claude Sonnet 4.6",
        "id": "anthropic/claude-sonnet-4.6",
        "vendor": "Anthropic",
        "efforts": ["low", "medium", "high", "max"],
        "default_effort": "medium",
    },
    {
        "key": "opus46",
        "label": "Claude Opus 4.6",
        "id": "anthropic/claude-opus-4.6",
        "vendor": "Anthropic",
        "efforts": ["low", "medium", "high", "max"],
        "default_effort": "high",
    },
    {
        "key": "gpt56sol",
        "label": "GPT-5.6 Sol",
        "id": "openai/gpt-5.6-sol",
        "vendor": "OpenAI",
        "efforts": ["none", "low", "medium", "high", "xhigh", "max"],
        "default_effort": "high",
    },
    {
        "key": "gpt56terra",
        "label": "GPT-5.6 Terra",
        "id": "openai/gpt-5.6-terra",
        "vendor": "OpenAI",
        "efforts": ["none", "low", "medium", "high", "xhigh", "max"],
        "default_effort": "high",
    },
    {
        "key": "gpt56luna",
        "label": "GPT-5.6 Luna",
        "id": "openai/gpt-5.6-luna",
        "vendor": "OpenAI",
        "efforts": ["none", "low", "medium", "high", "xhigh", "max"],
        "default_effort": "high",
    },
    {
        "key": "qwen38max",
        "label": "Qwen3.8 Max",
        "id": "qwen/qwen3.8-max",
        "vendor": "Alibaba",
        "efforts": ["low", "medium", "xhigh"],
        "default_effort": "xhigh",
    },
    {
        "key": "kimik3",
        "label": "Kimi K3",
        "id": "moonshot/kimi-k3",
        "vendor": "Moonshot AI",
        "efforts": ["low", "high", "max"],
        "default_effort": "max",
    },
]

DEFAULT_MODEL_KEY = "sonnet46"


def find_model(query: str):
    """Cari model berdasarkan nomor urut (1-based), key, atau id/label (partial, case-insensitive)."""
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


def get_model_by_key(key: str):
    for m in MODEL_CATALOG:
        if m["key"] == key:
            return m
    return MODEL_CATALOG[0]


def normalize_effort(raw: str):
    if not raw:
        return None
    return EFFORT_ALIASES.get(raw.strip().lower())


def closest_supported_effort(model: dict, effort: str) -> str:
    """Kalau effort yang diminta gak didukung model ini, cari yang paling deket dari daftar EFFORT_ORDER."""
    supported = model["efforts"]
    if effort in supported:
        return effort
    if effort not in EFFORT_ORDER:
        return model["default_effort"]
    target_idx = EFFORT_ORDER.index(effort)
    best = None
    best_dist = None
    for lvl in supported:
        dist = abs(EFFORT_ORDER.index(lvl) - target_idx)
        if best_dist is None or dist < best_dist:
            best = lvl
            best_dist = dist
    return best or model["default_effort"]
