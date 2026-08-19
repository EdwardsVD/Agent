# Agent CLI — Coding Agent dengan 🦸 24 SUPERPOWERS & Code Generator Engine

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Termux%20%7C%20Linux%20%7C%20macOS%20%7C%20Windows-green.svg)]()
[![Superpowers](https://img.shields.io/badge/Superpowers-24%20Skills-purple.svg)]()
[![Tests](https://img.shields.io/badge/Tests-101%20Passed-brightgreen.svg)]()

Coding agent CLI canggih yang **bukan cuma punya tools**, tapi memiliki **disiplin kerja tingkat tinggi (SOP Superpowers)** dan kemampuan **men-generate kode apa saja (Zero to One)** secara instan, modular, dan teruji langsung dari terminal HP (Termux) maupun Desktop (Linux/macOS/Windows).

---

## 💾 Link Download File .Zip

Kamu bisa langsung mengunduh source code lengkap versi terbaru dalam format `.zip`:

- 📦 **Download Direct Branch ZIP**: [Agent-v3.2.0 (Branch arena/01a01943-agent.zip)](https://github.com/EdwardsVD/Agent/archive/refs/heads/arena/01a01943-agent.zip)
- 📦 **File Zip Bundled di Repo**: `Agent-v3.2.0-superpowers.zip` (Tersedia langsung di root repository)

---

## 📱 Cara Install & Jalankan di TERMUX (Android)

Instalasi di Termux dibuat **100% anti-gagal, otomatis, dan tahan banting**:

### Opsi 1: Satu Baris Perintah (Rekomendasi)
Buka Termux dan tempel perintah ini:
```bash
pkg update -y && pkg install python git -y && git clone https://github.com/EdwardsVD/Agent.git && cd Agent && bash install.sh
```

### Opsi 2: Langkah demi Langkah (via `git clone`)
```bash
# 1. Pastikan Python & Git terpasang
pkg install python git -y

# 2. Clone repository Agent
git clone https://github.com/EdwardsVD/Agent.git

# 3. Masuk ke folder Agent
cd Agent

# 4. Jalankan installer otomatis (atau langsung launcher)
bash install.sh
```

Setelah terinstall, kamu bisa menjalankan Agent kapan saja cukup dengan mengetik:
```bash
agent
```
*(atau `bash run.sh` jika berada di dalam folder Agent)*

---

## 💻 Cara Install di Linux / macOS / Windows

```bash
git clone https://github.com/EdwardsVD/Agent.git
cd Agent
bash run.sh
```

---

## ✨ Yang Baru di v3.2.0 (Superpowers Code Generator Edition) 🚀

### 1. 🦸 24 Superpower Skills (Lengkap untuk Segala Kebutuhan Ngoding)
Agent dibekali 24 modul disiplin kerja & spesialisasi kode yang bisa dipanggil kapan saja:

| No | Skill | Alias Populer | Deskripsi / Kegunaan |
|:---:|---|---|---|
| 1 | `prompt-to-project` | `/gen`, `scaffold`, `p2p` | **Zero-to-One project scaffolding**: ubah prompt singkat jadi 1 proyek lengkap |
| 2 | `fullstack-code-generator` | `fullstack`, `webapp` | Bikin aplikasi fullstack (Frontend UI + Backend API + DB + Config) |
| 3 | `api-design-and-scaffolding` | `api`, `rest-api`, `swagger` | Desain REST/GraphQL API standar industri dengan validasi & OpenAPI spec |
| 4 | `database-architect` | `database`, `db`, `sqlite`, `sql` | Perancangan skema relasional/NoSQL, indexing, ORM models & migrasi |
| 5 | `code-refactoring-and-clean-code` | `refactor`, `clean-code`, `solid` | Refactoring kode ke prinsip SOLID, modularisasi, typing & docstrings |
| 6 | `frontend-ui-builder` | `frontend`, `ui`, `tailwind` | UI responsif mobile-first modern dengan Tailwind CSS & interactive JS |
| 7 | `security-and-vulnerability-hardening` | `security`, `audit`, `owasp` | Audit keamanan, anti-SQL injection, JWT auth, password hash & sanitasi |
| 8 | `scripting-and-automation` | `automation`, `script`, `scraper` | Skrip automasi Python/Bash, web scraper, cron jobs & utility CLI |
| 9 | `bot-and-integrations-builder` | `bot`, `telegram-bot`, `discord` | Pembuatan bot Telegram, Discord, WhatsApp & webhook listener |
| 10 | `reverse-engineering-and-analysis` | `reverse`, `explain-code` | Analisis codebase asing, tracing fungsi, & diagram alur Mermaid |
| 11 | `brainstorming` | `brainstorm`, `design` | Klarifikasi ide, spesifikasi, dan approval manusia sebelum eksekusi |
| 12 | `test-driven-development` | `tdd`, `test` | TDD sejati: Tulis test dulu (RED) -> Lihat gagal -> Tulis kode (GREEN) |
| 13 | `writing-plans` | `plan`, `todo` | Pembuatan breakdown rencana kerja terstruktur (todo checklist) |
| 14 | `systematic-debugging` | `debug`, `bug` | Pelacakan akar masalah (root cause) sistematis sebelum memodifikasi kode |
| 15 | `verification-before-completion` | `verify` | Pembuktian verifikasi segar dengan test/build sebelum selesai |
| 16 | `requesting-code-review` | `review` | Self-review komprehensif atas semua perubahan sebelum diserahkan |
| 17 | `receiving-code-review` | - | Penanganan feedback code review secara disiplin |
| 18 | `executing-plans` | `execute` | Eksekusi langkah rencana kerja tahap demi tahap |
| 19 | `finishing-a-development-branch` | `finish` | Verifikasi akhir sebelum merge atau submit PR |
| 20 | `using-git-worktrees` | `worktree` | Isolasi pengerjaan fitur baru dengan git worktrees |
| 21 | `using-superpowers` | `bootstrap` | Bootstrap awal pengenalan kapabilitas dan arsitektur harness |
| 22 | `writing-skills` | `write-skill` | Pembuatan dan pengujian skill superpowers baru |
| 23 | `dispatching-parallel-agents` | `parallel` | Panduan delegasi multi-tugas independen |
| 24 | `subagent-driven-development` | `subagent` | Arsitektur delegasi pengerjaan komponen |

---

### 2. ⚡ Perintah Instan Pembuatan Kode & Boilerplates

- **/generate `<prompt>`** (atau `/gen`): AI langsung merancang arsitektur, menulis seluruh file di `workspace/`, membuat unit test, dan menjalankan verifikasi sampai selesai.
- **/template `[nama]`** (atau `/tpl`): Buat template proyek instan:
  - `fastapi` — REST API FastAPI modern dengan Pydantic & Swagger
  - `flask` — REST Microservice Flask ringan
  - `react-tailwind` — Web SPA modern responsif dengan Tailwind CSS & dark mode
  - `termux-tool` — CLI utility Termux dengan integrasi baterai, storage & notifikasi Android
  - `sqlite-crud` — Database manager SQLite CRUD lengkap dengan parameter queries
  - `telegram-bot` — Boilerplate Bot Telegram dengan command handlers
  - `web-scraper` — Web scraper dengan user-agent rotation & JSON export
  - `pytest-suite` — Paket Python modular dengan test suite unittest/pytest
- **/prompt `[1-10]`** (atau `/presets`): Menu 10 panduan prompt siap pakai untuk pembuatan REST API, Web App, Scraper, Bot, Auth, dan lainnya.

---

### 3. 🛡 Zero-Dependency Fallback HTTP Engine
- Jika modul `requests` belum terpasang atau pip bermasalah di Termux, Agent **TIDAK AKAN CRASH**!
- Built-in HTTP shim berbasis `urllib` standar Python otomatis aktif dan menjalankan semua panggilan API & pencarian web dengan lancar.

---

### 4. 📱 Integrasi Penuh Termux & Android
- **Auto-Export ke Memori HP**: Setiap kali membuat file `.zip` via `/download` atau `/export`, file otomatis disalin langsung ke folder `Download/` HP (`/sdcard/Download` atau `~/storage/shared/Download`).
- **Android Notifications**: Mengirim notifikasi Android saat tugas selesai jika `termux-api` terpasang.
- **Clipboard Universal**: Perintah `/copy <file>` dan `/paste` terintegrasi dengan `termux-clipboard-set/get`, `pbcopy/pbpaste`, `xclip`, `wl-copy`, dan `clip`.
- **Ultra-Responsive Display**: Layout UI otomatis menyesuaikan layar sempit HP (30-50 kolom) tanpa baris yang patah.

---

### 5. 🧠 Model AI Terbaru & Custom Gateway
Daftar model yang didukung di `/models` dan `/model <nama>`:
- `sonnet37` — Claude 3.7 Sonnet (Anthropic)
- `sonnet35` — Claude 3.5 Sonnet (Anthropic)
- `gpt4o` — GPT-4o (OpenAI)
- `gpt4omini` — GPT-4o Mini (OpenAI)
- `o3mini` — o3-mini Reasoning (OpenAI)
- `deepseekr1` — DeepSeek R1 Reasoning (DeepSeek)
- `deepseekv3` — DeepSeek V3 (DeepSeek)
- `qwencoder` — Qwen 2.5 Coder 32B (Alibaba)
- `gemini2flash` — Gemini 2.0 Flash (Google)
- `llama33` — Llama 3.3 70B (Meta)
- **Model Custom Bebas**: Bisa masukkan model ID apa saja lewat `/model custom/id` atau Ollama lokal!

---

## 📋 Daftar Perintah Lengkap (Slash Commands)

| Perintah | Deskripsi |
|---|---|
| `/help` | Menampilkan panduan bantuan lengkap |
| `/skills` | Menampilkan 24 skill Superpowers yang aktif |
| `/skills <nama>` | Membaca isi lengkap satu skill (misal `/skills fullstack`) |
| `/generate <prompt>` | Meminta AI membuat proyek/kode lengkap secara instan |
| `/template [nama]` | Membuat boilerplate proyek di folder `workspace/` |
| `/prompt [no]` | Memilih preset prompt panduan pembuatan kode |
| `/refactor <file>` | Merefaktor file dengan prinsip Clean Code & SOLID |
| `/testgen <file>` | Membuat file unit test otomatis untuk kode yang dipilih |
| `/explain <file>` | Menganalisis arsitektur dan cara kerja kode |
| `/fix <file>` | Mendiagnosis bug dan memperbaiki error otomatis |
| `/export` atau `/zip` | Membungkus seluruh isi workspace ke dalam file `.zip` |
| `/copy <file>` | Menyalin isi file workspace ke clipboard sistem / Termux |
| `/paste [file]` | Menempelkan isi clipboard ke file baru di workspace |
| `/diff [file]` | Menampilkan perbedaan perubahan file (git diff) |
| `/snippet [list\|save\|show]` | Manajemen koleksi potongan kode |
| `/stats` | Menampilkan statistik sesi, token, dan status sistem |
| `/doctor` | Cek diagnostik kesehatan instalasi & Termux |
| `/models` | Melihat daftar model AI yang tersedia |
| `/model <nama>` | Mengganti model AI yang aktif |
| `/think on\|off` | Mengaktifkan/mematikan reasoning model |
| `/think show\|hide` | Membuka/menutup tampilan pemikiran AI |
| `/connect` | Menghubungkan API Key (Xkiro, OpenAI, OpenRouter, dll) |
| `/clear` | Membersihkan riwayat percakapan |
| `/exit` | Keluar dari program Agent |
| `!<command>` | Menjalankan perintah bash langsung (misal: `!ls -la`) |

---

## 🧪 Pengujian & Kehandalan (101 Tests Passed)

Seluruh komponen diuji dengan unit test komprehensif:
```bash
python3 -m unittest discover -s tests -v
```

Hasil pengujian: **101 tests passed (100% OK)** mencakup:
- 24 Superpower skills discovery & resolution
- Hard-gate blocking & anti-gaming verification
- Zero-dependency requests shim
- Template & prompt preset generators
- Termux mobile formatting & diagnostics
- File system safety & workspace sandboxing

---

## 📄 Lisensi
- Kode Harness Agent: MIT License
- Superpower Skills: MIT License © Jesse Vincent (obra/superpowers)
