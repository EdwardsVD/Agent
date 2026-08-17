# opencode-clone (versi sederhana, Python-only)

Coding agent CLI minimalis dengan tampilan chat + toolbar di terminal, siap
disambungkan ke gateway **Xkiro.com** (satu API key untuk banyak model).

## Fitur

- Format balasan AI ketat: `ACTION/INPUT` (panggil tool) atau `DONE:` (selesai) — tanpa tebak-tebakan.
- Tool sandbox: `read_file`, `write_file`, `edit_file`, `bash` (dibatasi ke `python-agent/sandbox_workspace/`).
- **Toolbar status** di atas prompt: model aktif, level upaya (effort), status thinking, status koneksi.
- **Chat user** ditampilkan dengan **background biru**; balasan agent & log tool pakai warna berbeda biar gampang dibaca.
- Slash-command untuk kontrol penuh tanpa keluar dari chat.
- Template `/connect` siap pakai untuk **Xkiro.com**.
- Daftar model lengkap + kontrol **thinking ON/OFF** dan **level upaya** (low/medium/high/xhigh≈extreme/max).

## Instalasi

```bash
cd python-agent
pip install -r requirements.txt
```

## Menjalankan

```bash
export XKIRO_API_KEY="sk-xkiro-xxxxxxxx"   # opsional, bisa juga diisi lewat /connect
python agent.py
```

## Slash-command

| Perintah | Fungsi |
|---|---|
| `/connect` | Wizard interaktif setup base URL + API key (default sudah diarahkan ke Xkiro) |
| `/connect show` | Lihat konfigurasi koneksi saat ini (key disamarkan) |
| `/connect test` | Tes koneksi (`GET /v1/models`) pakai konfigurasi aktif |
| `/models` | Lihat semua model yang tersedia beserta level upaya yang didukung |
| `/model <no|nama>` | Ganti model aktif, mis. `/model kimik3` atau `/model 6` |
| `/think on` / `/think off` | Nyalakan / matikan reasoning (thinking) model |
| `/effort <level>` | Atur kedalaman berpikir: `none, low, medium, high, xhigh (extreme), max` |
| `/status` | Tampilkan ulang toolbar status |
| `/clear` | Kosongkan riwayat percakapan |
| `/help` | Tampilkan bantuan |
| `/exit` / `/quit` | Keluar |

Konfigurasi koneksi disimpan persist di `~/.opencode_clone/connect.json`.

## Daftar model (via Xkiro.com)

| # | Label | Model ID | Vendor | Level upaya didukung |
|---|---|---|---|---|
| 1 | Claude Fable 5 | `anthropic/claude-fable-5` | Anthropic | low, medium, high, xhigh, max |
| 2 | Claude Opus 5 | `anthropic/claude-opus-5` | Anthropic | low, medium, high, xhigh, max |
| 3 | Claude Sonnet 5 | `anthropic/claude-sonnet-5` | Anthropic | low, medium, high, xhigh, max |
| 4 | Claude Sonnet 4.6 | `anthropic/claude-sonnet-4.6` | Anthropic | low, medium, high, max |
| 5 | Claude Opus 4.6 | `anthropic/claude-opus-4.6` | Anthropic | low, medium, high, max |
| 6 | GPT-5.6 Sol | `openai/gpt-5.6-sol` | OpenAI | none, low, medium, high, xhigh, max |
| 7 | GPT-5.6 Terra | `openai/gpt-5.6-terra` | OpenAI | none, low, medium, high, xhigh, max |
| 8 | GPT-5.6 Luna | `openai/gpt-5.6-luna` | OpenAI | none, low, medium, high, xhigh, max |
| 9 | Qwen3.8 Max | `qwen/qwen3.8-max` | Alibaba | low, medium, xhigh |
| 10 | Kimi K3 | `moonshot/kimi-k3` | Moonshot AI | low, high, max |

Kalau level upaya yang diminta tidak didukung model tertentu, agent otomatis
memetakan ke level terdekat yang tersedia.

## Cara kerja koneksi API

Agent memanggil endpoint OpenAI-compatible milik Xkiro:

```
POST https://api.xkiro.com/v1/chat/completions
Authorization: Bearer <XKIRO_API_KEY>
Content-Type: application/json

{
  "model": "anthropic/claude-sonnet-4.6",
  "messages": [...],
  "max_tokens": 1024,
  "reasoning": {"effort": "high"}      // atau {"enabled": false} kalau /think off
}
```

## Struktur file

```
python-agent/
├── agent.py         # entry point, REPL, slash-command, loop ACTION/DONE
├── ui.py            # toolbar + chat bubble (user = background biru)
├── config.py        # load/save konfigurasi + wizard /connect (template Xkiro.com)
├── models.py        # katalog 10 model + level upaya
├── api_client.py    # pemanggil HTTP ke Xkiro (chat/completions)
├── tools.py         # tool sandbox: read_file, write_file, edit_file, bash
└── requirements.txt
```
