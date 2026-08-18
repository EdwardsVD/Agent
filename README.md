# Agent CLI — coding agent 1 file Python (thinking + AI search)

Coding agent CLI minimalis, **semua fitur dalam satu file `main.py`**.
Agent bisa **berpikir (thinking) yang ditampilkan jelas** — bisa dibuka/ditutup —
dan **mencari di web sendiri** (DuckDuckGo / SearXNG) dengan alur:

```
🧠 Thinking → 🔎 Search → 🧠 Thinking lagi → ✅ Hasil
```

Contoh tampilan pas agent lagi ngerjain tugas:

```
🧠 Thinking ──────────────────────────────────────────
 Sepertinya ada yang kurang......
──────────────────────────────────────────────────────
🔎 Search "blablablabla.com" (limit=5, engine=auto)
  ↳ 5 hasil untuk "blablablabla.com" via DDG
    1. Blablablabla Docs
       https://blablablabla.com/docs
       ...
📄 Fetch https://blablablabla.com/docs
  ↳ [OK] Blablablabla Docs — https://...
🧠 Thinking ──────────────────────────────────────────
 Semua data cukup, menyusun jawaban final.
──────────────────────────────────────────────────────
 DONE ────────────────────────────────────────────────
  Jawaban lengkap + sumber [1](url), [2](url)
```

## Instalasi & menjalankan

```bash
git clone https://github.com/EdwardsVD/Agent.git
cd Agent
pip install -r requirements.txt
python3 main.py
```

Hanya butuh **1 dependency**: `requests`. Sisanya Python stdlib.

Saat pertama jalan, konekin API key dulu:

```bash
export XKIRO_API_KEY="sk-..."    # opsional, bisa juga lewat /connect
```

atau langsung ketik `/connect` di dalam program (template Xkiro.com — satu API
key buat banyak model: Claude, GPT, Qwen, Kimi).

## Fitur utama

- **Thinking diperlihatkan** — reasoning model ditampilkan sebagai blok 🧠 yang
  jelas. Bisa dibuka/tutup kapan aja:
  - `/think on|off` — aktifkan/matikan reasoning model
  - `/think show|hide|toggle` — tampilkan/sembunyikan blok thinking
    (pas disembunyikan tetap dihitung jumlah katanya, bisa dibuka lagi)
- **AI search built-in** — model bisa cari info sendiri pas ngerjain tugas:
  - `web_search` via **DuckDuckGo** (tanpa API key, langsung jalan) atau
    **SearXNG** (instance sendiri, lebih privat/anti-blok)
  - `web_fetch` buat baca isi halaman hasil pencarian
  - Hasil search masuk ke konteks → model mikir lagi → jawaban lebih akurat
    dengan **sumber [1](url)** di jawaban final
- **Tool sandbox** — `read_file`, `write_file`, `edit_file` (pencocokan fuzzy,
  toleran whitespace/indentasi), `bash` — semua dibatasi di folder `workspace/`
- **Streaming respons** + fallback otomatis ke non-stream kalau provider nolak
- **Toolbar status** — model aktif, level upaya, status thinking, engine search,
  jumlah langkah, status koneksi
- **10 model** via Xkiro.com + kontrol effort: `none, low, medium, high, xhigh, max`
- Slash-command lengkap, riwayat percakapan multi-turn, konfigurasi persist di
  `~/.opencode_clone/connect.json`

## Slash-command

| Perintah | Fungsi |
|---|---|
| `/connect` | Wizard setup base URL + API key (default Xkiro.com) |
| `/connect show` / `/connect test` | Lihat / tes koneksi |
| `/models` | Daftar semua model + level upaya yang didukung |
| `/model <no\|nama>` | Ganti model, mis. `/model kimik3` atau `/model 6` |
| `/think on` / `/think off` | Aktifkan / matikan reasoning model |
| `/think show` / `/think hide` / `/think toggle` | **Buka / tutup tampilan blok thinking** |
| `/effort <level>` | `none, low, medium, high, xhigh, max` |
| `/search` | Lihat pengaturan AI search |
| `/search ddg` / `/search auto` | Pilih engine: DDG saja / auto (SearXNG kalau di-set) |
| `/search searxng <url>` | Pakai instance SearXNG sendiri (mis. `http://localhost:8080`) |
| `/search searxng off` | Matikan SearXNG, balik ke DDG |
| `/search test <query>` | Coba cari langsung (5 hasil) tanpa manggil model |
| `/fetch <url>` | Coba ambil isi halaman web langsung |
| `/limit <n>` | Maks. langkah agent per tugas (default 30) |
| `/status` | Status lengkap (model, thinking, search, endpoint, key) |
| `/clear` | Kosongkan riwayat percakapan |
| `/help` | Bantuan |
| `/exit` / `/quit` | Keluar |

## Setup SearXNG

DuckDuckGo jalan tanpa konfigurasi. Kalau mau pakai SearXNG (instance sendiri
atau publik):

```bash
# lewat perintah di dalam program:
/search searxng https://searx.example.com

# atau lewat environment variable:
export SEARXNG_URL="https://searx.example.com"
```

Kalau SearXNG gagal, agent otomatis fallback ke DDG (ada catatannya di hasil).

## Daftar model (via Xkiro.com)

| # | Label | Model ID | Level upaya |
|---|---|---|---|
| 1 | Claude Fable 5 | `anthropic/claude-fable-5` | low, medium, high, xhigh, max |
| 2 | Claude Opus 5 | `anthropic/claude-opus-5` | low, medium, high, xhigh, max |
| 3 | Claude Sonnet 5 | `anthropic/claude-sonnet-5` | low, medium, high, xhigh, max |
| 4 | Claude Sonnet 4.6 | `anthropic/claude-sonnet-4.6` | low, medium, high, max |
| 5 | Claude Opus 4.6 | `anthropic/claude-opus-4.6` | low, medium, high, max |
| 6 | GPT-5.6 Sol | `openai/gpt-5.6-sol` | none, low, medium, high, xhigh, max |
| 7 | GPT-5.6 Terra | `openai/gpt-5.6-terra` | none, low, medium, high, xhigh, max |
| 8 | GPT-5.6 Luna | `openai/gpt-5.6-luna` | none, low, medium, high, xhigh, max |
| 9 | Qwen3.8 Max | `qwen/qwen3.8-max` | low, medium, xhigh |
| 10 | Kimi K3 | `moonshot/kimi-k3` | low, high, max |

Kalau level upaya tidak didukung model, otomatis dipetakan ke yang terdekat.

## Cara kerja

Agent manggil endpoint OpenAI-compatible (`POST {base_url}/chat/completions`)
dengan parameter `reasoning` buat kontrol thinking:

```json
{
  "model": "anthropic/claude-sonnet-4.6",
  "messages": [...],
  "max_tokens": 4096,
  "reasoning": {"effort": "high"}      // atau {"enabled": false} kalau /think off
}
```

Alur per tugas: model berpikir (blok 🧠 ditampilkan), kalau butuh info dia
panggil `web_search` → hasil masuk sebagai OBSERVATION → model berpikir lagi
(bisa `web_fetch` halaman relevan) → jawab `DONE` lengkap dengan sumber.
Reasoning model dibaca dari field `reasoning_content` / `reasoning` / `thinking`
(pakai streaming SSE, fallback non-stream otomatis).

## Struktur file

```
Agent/
├── main.py            # SEMUA kode agent (1 file)
├── requirements.txt   # cuma requests
├── README.md
└── workspace/         # folder kerja agent (dibuat otomatis, di-gitignore)
```
