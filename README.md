# Agent CLI — coding agent Python dengan 🦸 SUPERPOWERS

Coding agent CLI yang **bukan cuma punya tools**, tapi punya **disiplin kerja**.

Kebanyakan agent CLI kalau dikasih tugas langsung nyemplung ngoding. Agent ini
**gak bisa** — dia dipaksa lewat SOP yang sama kayak Superpowers-nya Claude Code:

```
🦸 Baca skill → 🙋 Brainstorm + minta persetujuan kamu → 📋 Bikin rencana
→ 🔴 Test dulu (TDD) → 🟢 Baru kode → ✅ Jalanin bukti verifikasi
→ 📖 Baca ulang hasil sendiri → DONE
```

Kalau dia coba nyalip alur, **aksinya di-block** dan muncul 🛑 GATE.

Ditambah yang udah ada: thinking yang kelihatan, AI search (DDG/SearXNG),
animasi hacker, dan download hasil kerja dalam zip.

## Yang baru di v3.1.0 🚑

- **Fix error Termux `Agent/Agent/main.py`** — ada `run.sh` (launcher yang selalu
  pindah ke folder bener, boleh dijalanin dari mana aja) + `--doctor` /`/doctor`
  yang ngasih tau persis apa yang salah dan cara benerinnya.
- **Fix layar HP kepotong** — dulu lebar terminal dipaksa minimal 50 kolom, jadi
  panel jebol ke samping di layar HP sempit. Sekarang ngikut layar (min 24).
- **Fix gate bisa diakalin** (2 bug beneran):
  - `python3 --version` / `echo ok` dulu dihitung sebagai "bukti verifikasi".
    Sekarang ditolak — cuma test/build/lint beneran yang ngitung.
  - File test kosong atau cuma `pass` dulu bisa lolos gate TDD. Sekarang harus
    ada assertion beneran.
- **Skill dilengkapi** — 14 skill + semua resource pendukungnya (42 file, dulu
  cuma 29): `references/`, `examples/`, `anthropic-best-practices.md`, script
  debug, dll. Plus `references/agent-cli-tools.md` (ditulis khusus buat harness
  ini) yang ngasih tau agent skill subagent gak bisa dipakai mentah-mentah —
  jadi dia gak ngarang punya subagent.
- `--help`, `-V`, dan pesan error yang nolongin, bukan bikin bingung.

## Fitur v3.0.0 — SUPERPOWERS 🦸

Versi sebelumnya cuma setara "OpenCode versi minimalis": rangkanya ada, tools-nya
ada, tapi **metodologinya gak ada**. v3.0.0 nambahin bagian yang justru jadi inti
Superpowers — **SOP kerja yang nempel di atas rangka itu**.

### 1. Skill library beneran (14 skill dari obra/superpowers)

Skill markdown asli di-**vendor** ke folder `skills/`, jadi `git clone` langsung
jalan di Termux tanpa internet dan tanpa npm:

| Skill | Gunanya |
|---|---|
| `brainstorming` | Wajib sebelum kerjaan kreatif — klasifikasi spike/bounded/architectural, tanya, desain, **approval gate** |
| `test-driven-development` | RED → GREEN → REFACTOR. *No production code without a failing test first* |
| `writing-plans` | Pecah spec jadi task kecil yang bisa dieksekusi |
| `executing-plans` | Jalanin plan dengan checkpoint |
| `systematic-debugging` | *No fixes without root cause first* — jangan nambal gejala |
| `verification-before-completion` | *No completion claims without fresh verification evidence* |
| `requesting-code-review` / `receiving-code-review` | Review kerjaan sebelum ngaku beres |
| `subagent-driven-development` | Kerjain plan lewat subagent |
| `dispatching-parallel-agents` | Tugas independen dikerjain paralel |
| `using-git-worktrees` | Workspace terisolasi |
| `finishing-a-development-branch` | Nutup kerjaan dengan benar |
| `using-superpowers` | Bootstrap yang bikin skill auto-trigger |
| `writing-skills` | Bikin skill baru |

Agent baca skill **on-demand** (progressive disclosure) lewat tool `skill` —
yang masuk ke system prompt cuma nama + deskripsinya, jadi context gak jebol.

### 2. Workflow gates — SOP yang dipaksa, bukan disaranin

Prompt doang gampang diabaikan model. Makanya ada **5 gate keras di level kode**
yang beneran nge-block aksi agent:

| Gate | Kapan nge-block |
|---|---|
| 🛑 `using-superpowers` | Mau nulis file tapi belum invoke skill apa pun |
| 🛑 `brainstorming` HARD-GATE | Mau nulis kode tapi belum dapat persetujuan kamu |
| 🛑 `test-driven-development` | Mau nulis kode produksi tapi belum ada test |
| 🛑 `writing-plans` | Mau bilang DONE tapi gak ada rencana yang kelihatan |
| 🛑 `verification-before-completion` | Mau bilang DONE tapi file diubah sesudah verifikasi terakhir |
| 🛑 `requesting-code-review` | Mau bilang DONE tapi belum baca ulang hasil sendiri |

Tiap gate ada batas berapa kali boleh nembak, jadi agent gak kejebak loop.
Matikan kapan aja: `/superpowers gates off`.

### 3. Tool baru

- `skill {"name": "tdd"}` — baca isi skill (+ `"resource"` buat file pendukung)
- `list_skills {}` — lihat semua skill
- `todo_write {"todos": [...]}` — checklist kerja, tampil rapi di terminal
- `ask_user {"question": "...", "options": [...]}` — **agent nanya balik ke kamu**
  dan nunggu jawaban. Ini yang bikin approval gate beneran jalan.

### 4. Struk kerja di akhir tugas

Tiap DONE, agent nunjukin catatan: skill apa yang dipakai, berapa approval,
berapa task beres, dan **perintah verifikasi apa yang beneran dijalanin**.

### Masih ada semua dari v2.1.0

Intro animasi matrix + logo AGENT + loading, thinking yang bisa dibuka/tutup,
AI search DDG/SearXNG, `/download` zip, bash langsung pakai `!`.

Contoh tampilan pas agent lagi ngerjain tugas (perhatiin gate-nya):

```
You › bikin fungsi buat validasi email

🧠 Thinking ──────────────────────────────────────────
 Ini kerjaan kreatif, cek skill dulu.
──────────────────────────────────────────────────────
🦸 Skill brainstorming

🙋 Butuh keputusan kamu ───────────────────────────────
 Ini bounded. Rencana: bikin validate_email() di email.py,
 test di test_email.py, cek format + domain. Setuju?
   1. Setuju, lanjut
   2. Ubah dulu
Jawab › 1

📋 Rencana kerja  (0/3 beres)
  ○ Tulis test buat validate_email()
  ○ Lihat test-nya MERAH
  ○ Implementasi sampai HIJAU

📝 Tulis calc.py
🛑 GATE [test-driven-development] — DITOLAK:
   NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST.
   Tulis test-nya dulu, jalanin, lihat dia GAGAL.

📝 Tulis test_email.py
💻 Bash python3 -m pytest test_email.py     ← 🔴 MERAH (bener, fiturnya belum ada)
📝 Tulis email.py
💻 Bash python3 -m pytest test_email.py     ← 🟢 HIJAU, 4 passed
📖 Baca email.py                            ← self review

 DONE ────────────────────────────────────────────────
 validate_email() dibuat. Bukti: pytest → 4 passed.

 🦸 Superpowers — catatan kerja
   Skill dipakai : brainstorming, test-driven-development
   Approval      : 1x dari partner manusia
   Rencana       : 3/3 task beres
   File disentuh : 2
   Bukti verifikasi (2):
     ✔ python3 -m pytest test_email.py

💾 Click here to download: /download
```

## Instalasi & menjalankan

```bash
git clone https://github.com/EdwardsVD/Agent.git
cd Agent
pip install -r requirements.txt
python main.py
```

Cuma **1 dependency** (`requests`), sisanya Python stdlib. Skill Superpowers udah
ikut di dalam repo (folder `skills/`) — **gak perlu download apa-apa lagi, gak
butuh npm**.

### 📱 Termux (Android) — cara paling anti-gagal

```bash
pkg update -y && pkg install python git -y
cd ~
git clone https://github.com/EdwardsVD/Agent.git
cd Agent
bash run.sh
```

**`bash run.sh`** itu launcher yang:
- selalu pindah ke folder Agent yang bener dulu (jadi **gak mungkin** kena error
  `Agent/Agent/main.py`), boleh dijalanin dari folder mana aja
- otomatis cari `python3` **atau** `python` (Termux kadang cuma punya `python`)
- otomatis `pip install` kalau `requests` belum ada
- ngingetin kalau folder `skills/` gak keikut

---

## 🚑 Kena error `can't open file '.../Agent/Agent/main.py'`?

```
python: can't open file '/data/data/com.termux/files/home/Agent/Agent/main.py':
[Errno 2] No such file or directory
~/Agent/Agent $
```

**Penyebabnya:** kamu lagi ada di folder `~/Agent/Agent` yang **kosong**. Ini
biasanya kejadian karena clone pertama gagal/keinterupsi (sinyal putus, kehabisan
kuota, Ctrl-C), atau kamu terlanjur `git clone` lagi dari dalam folder `Agent`.
Perhatiin prompt-nya: ada `Agent/Agent` — itu tandanya kamu **kelewat satu folder
ke dalam**.

**Cek dulu kamu di mana:**

```bash
pwd      # kalau ujungnya /Agent/Agent -> kamu kejebak
ls       # kalau kosong / gak ada main.py -> bener, kejebak
```

### Cara cepat (tanpa download ulang)

```bash
cd ~/Agent          # naik satu folder
ls                  # main.py harusnya keliatan di sini
bash run.sh
```

Masih bingung? Jalanin dokternya, dia bakal bilang persis apa yang salah:

```bash
python ~/Agent/main.py --doctor
```

### Cara pasti (clone ulang bersih)

```bash
cd ~
rm -rf Agent
git clone https://github.com/EdwardsVD/Agent.git
cd Agent
bash run.sh
```

> ⚠️ **Aturan biar gak kejadian lagi:** jalanin `git clone` dari **home** (`cd ~`),
> **bukan** dari dalam folder `Agent`. Kalau `git clone` dijalanin di dalam
> `~/Agent`, hasilnya jadi `~/Agent/Agent` dan kamu bakal bingung lagi.

---

### Cek instalasi bener apa enggak

```bash
python main.py --doctor                  # 🩺 laporan lengkap
python main.py --version                 # -> Agent CLI v3.1.0
python3 -m unittest discover -s tests    # -> Ran 89 tests ... OK
```

Terus di dalam program ketik `/skills` — harus muncul **14 skill**.

### Konek API

```bash
export XKIRO_API_KEY="sk-..."    # opsional, bisa juga lewat /connect
```

atau ketik `/connect` di dalam program (template Xkiro.com — satu API key buat
banyak model: Claude, GPT, Qwen, Kimi).

## Fitur utama

- 🦸 **Superpowers — metodologi kerja** (ini yang bikin beda):
  - 14 skill markdown asli dari [obra/superpowers](https://github.com/obra/superpowers),
    dibaca on-demand (progressive disclosure) — context gak jebol
  - 5 **workflow gate** di level kode yang beneran nge-block agent kalau nyalip
    alur: skill check, approval, TDD, rencana, verifikasi, self-review
  - `ask_user` — agent nanya balik & **nunggu jawaban kamu** sebelum ngoding
  - `todo_write` — checklist kerja yang tampil rapi dan ke-update sambil jalan
  - Struk kerja di akhir tugas: skill dipakai, approval, bukti verifikasi
  - Bisa dimatiin: `/superpowers off` (mode polos) atau `/superpowers gates off`
- **Intro animasi** — matrix hijau full screen + logo AGENT + loading 1-100%
  (`/intro` buat replay, `--no-anim` buat skip)
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
- **Superpower tools** — `list_files`, `grep_files`, `read_file` (offset/limit),
  `write_file`, `edit_file` (pencocokan fuzzy, toleran whitespace), `bash`
  (timeout sampai 600 dtk, ada exit code) — file dibatasi di folder `workspace/`
- **Download hasil kerja** — `/download -f <file>` (zip otomatis),
  `/download` (zip semua file tugas terakhir), `/download list`
- **Streaming respons** + fallback otomatis ke non-stream kalau provider nolak
- **Toolbar status** — model aktif, level upaya, status thinking, engine search,
  jumlah langkah, status koneksi
- **10 model** via Xkiro.com + kontrol effort: `none, low, medium, high, xhigh, max`
- Slash-command lengkap, riwayat percakapan multi-turn, bash cepat dengan `!`,
  konfigurasi persist di `~/.opencode_clone/connect.json`

## Slash-command

| Perintah | Fungsi |
|---|---|
| `/skills` | 🦸 **Lihat 14 skill Superpowers yang dimuat** |
| `/skills <nama>` | Baca isi 1 skill, mis. `/skills tdd`, `/skills brainstorming` |
| `/doctor` | 🩺 Cek instalasi kalau ada yang aneh |
| `/skills <nama> <file>` | Baca resource skill, mis. `/skills tdd writing-good-tests.md` |
| `/superpowers` | Status metodologi (on/off, gates, jumlah skill) |
| `/superpowers on` / `off` | Nyalakan / matikan metodologi Superpowers |
| `/superpowers gates on` / `off` | Gate keras on/off (SOP tetap di prompt) |
| `/superpowers reload` | Muat ulang skill dari folder `skills/` |
| `/intro` | Putar ulang animasi pembuka (matrix + loading) |
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
| `/download -f <file>` | **ZIP file hasil kerja agent** (ke folder `downloads/`) |
| `/download` | ZIP semua file yang dibuat di tugas terakhir |
| `/download list` | Lihat daftar file yang bisa di-download |
| `/limit <n>` | Maks. langkah agent per tugas (default 40) |
| `/status` | Status lengkap (model, thinking, search, endpoint, key) |
| `/clear` | Kosongkan riwayat percakapan |
| `/help` | Bantuan |
| `/exit` / `/quit` | Keluar |
| `!<command>` | Jalankan bash langsung, contoh `!ls -la` |

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

### Alur per tugas (Superpowers ON)

1. **Skill check** — agent mikir "skill mana yang relevan?" lalu `skill {"name": …}`.
   Kalau dia skip dan langsung nulis file → 🛑 gate `using-superpowers`.
2. **Brainstorm + approval** — klasifikasi (spike/bounded/architectural), tanya
   lewat `ask_user`, presentasi desain singkat, **tunggu kamu bilang iya**.
   Nulis kode sebelum approval → 🛑 gate `brainstorming` HARD-GATE.
3. **Rencana** — `todo_write` pecah jadi task kecil, status ke-update sambil jalan.
4. **Eksplorasi & riset** — `list_files`/`grep_files`/`read_file`, `web_search` +
   `web_fetch` kalau butuh fakta terkini.
5. **TDD** — test dulu → jalanin → **lihat MERAH** → kode minimal → **HIJAU**.
   Nulis kode produksi sebelum ada test → 🛑 gate `test-driven-development`.
6. **Verifikasi** — `bash` jalanin pytest/npm test/py_compile/lint, baca outputnya.
   Ngaku selesai tanpa bukti segar → 🛑 gate `verification-before-completion`.
7. **Self review** — `read_file` hasil kerjanya sendiri, cek ke permintaan awal.
8. **DONE** — ringkasan + file + **bukti verifikasi** + sumber + tawaran zip.

Gate-nya dicek di level kode (`pre_action_gate` / `pre_done_gate` di `main.py`),
bukan cuma imbauan di prompt — makanya model gak bisa ngeles. Tiap gate punya
jatah nembak terbatas biar agent gak kejebak loop.

Reasoning model dibaca dari field `reasoning_content` / `reasoning` / `thinking`
(streaming SSE, fallback non-stream otomatis).

## Struktur file

```
Agent/
├── run.sh                   # 🚑 launcher anti-gagal (pakai ini di Termux)
├── main.py                  # SEMUA kode agent: harness + skill loader + gates
├── skills/                  # 🦸 skill Superpowers (WAJIB ikut ke-clone!)
│   ├── brainstorming/SKILL.md
│   ├── test-driven-development/SKILL.md
│   ├── systematic-debugging/SKILL.md
│   ├── verification-before-completion/SKILL.md
│   ├── using-superpowers/references/agent-cli-tools.md   # adaptasi harness ini
│   ├── … (14 skill, 42 file total)
│   ├── NOTICE.md            # asal-usul & cara update skill
│   └── LICENSE-superpowers.txt
├── tests/
│   └── test_superpowers.py  # 89 test buat mesin Superpowers
├── requirements.txt         # cuma requests
├── README.md
├── workspace/               # folder kerja agent (otomatis, di-gitignore)
└── downloads/               # hasil /download (zip, otomatis, di-gitignore)
```

## Kredit & lisensi

Harness (`main.py`, skill loader, workflow gates, tools) — MIT, lihat `LICENSE`.

Isi folder `skills/` di-vendor apa adanya dari
**[obra/superpowers](https://github.com/obra/superpowers)** v6.3.0 —
MIT License, Copyright (c) 2025 Jesse Vincent. Teks skill **tidak diubah**
sama sekali. Detail lengkap di `skills/NOTICE.md`.
