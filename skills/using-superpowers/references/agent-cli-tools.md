## Agent CLI (harness ini) — cara skill dipetakan ke tool yang ada

Kamu jalan di **Agent CLI**, harness Python satu-file. Beberapa skill Superpowers
ditulis buat harness yang punya subagent (Claude Code, Codex, Gemini CLI).
Harness ini **belum punya subagent**. Berikut terjemahannya.

### Tool yang tersedia

| Yang disebut skill | Di sini pakai |
|---|---|
| Read / View | `read_file {"path": ..., "offset": 0, "limit": 0}` |
| Write | `write_file {"path": ..., "content": ...}` |
| Edit / Str-replace | `edit_file {"path": ..., "old": ..., "new": ...}` (fuzzy, toleran whitespace) |
| Glob / LS | `list_files {"path": ".", "depth": 3}` |
| Grep | `grep_files {"pattern": ..., "path": ".", "regex": false}` |
| Bash / Shell | `bash {"command": ..., "timeout": 120}` (maks 600 dtk) |
| WebSearch | `web_search {"query": ..., "limit": 5}` |
| WebFetch | `web_fetch {"url": ...}` |
| TodoWrite | `todo_write {"todos": [{"task": ..., "status": ...}]}` |
| AskUserQuestion | `ask_user {"question": ..., "options": [...]}` |
| Skill | `skill {"name": ..., "resource": ...}` |

### Tidak ada subagent — apa artinya

Skill `subagent-driven-development` dan `dispatching-parallel-agents` **tidak bisa
dijalankan apa adanya**. Jangan pura-pura punya subagent, jangan mengarang hasil
review dari "agent lain".

Gantinya:

- **Sebagai ganti `subagent-driven-development`** → pakai `executing-plans`.
  Kerjakan task plan satu per satu di sesi ini, verifikasi tiap task selesai.
- **Sebagai ganti `requesting-code-review` via subagent** → lakukan review
  sendiri dengan mata segar: `read_file` ulang tiap file yang kamu ubah, baca
  `requesting-code-review/code-reviewer.md` sebagai checklist, dan laporkan
  temuan jujur (termasuk yang bikin kamu keliatan salah).
- **Sebagai ganti `dispatching-parallel-agents`** → kerjakan berurutan. Bilang
  ke partner manusia kalau tugasnya sebenarnya paralel tapi harness ini serial.

### Tidak ada plan mode / git worktree otomatis

- `using-git-worktrees` opsional di sini. Workspace agent dibatasi ke folder
  `workspace/`. Kalau partner manusia kerja di repo git beneran, sarankan
  worktree tapi jangan paksa.
- Approval gate dijalankan lewat `ask_user`, bukan lewat plan-mode harness.

### Workflow gate yang dipaksa di level kode

Harness ini **menegakkan** sebagian skill lewat kode, bukan cuma imbauan. Kalau
kamu nyalip alur, aksimu **ditolak** dan kamu dapat pesan `🛑 GATE [...]`:

| Gate | Nyala kalau |
|---|---|
| `using-superpowers` | Mau nulis file tapi belum invoke skill apa pun |
| `brainstorming` HARD-GATE | Mau nulis kode tapi belum ada approval dari `ask_user` |
| `test-driven-development` | Mau nulis kode produksi tapi belum ada file test |
| `writing-plans` | Mau DONE tapi belum pernah `todo_write` |
| `verification-before-completion` | Mau DONE tapi file berubah sesudah verifikasi terakhir |
| `requesting-code-review` | Mau DONE tapi belum `read_file` hasil kerjamu |

**Jangan cari cara mengakali gate.** Menamai file produksi seolah-olah file test,
atau menjalankan perintah kosong biar dianggap verifikasi, itu melanggar semangat
aturannya. Kerjakan yang diminta gate, lalu lanjut.

### Bukti verifikasi yang dihitung

Harness cuma menghitung perintah `bash` yang **berhasil** (exit code 0) dan
kelihatan seperti verifikasi: `pytest`, `unittest`, `npm test`, `jest`, `vitest`,
`go test`, `cargo test`, `py_compile`, `node --check`, `bash -n`, linter, build.
Perintah yang gagal **tidak** dihitung sebagai bukti — itu memang disengaja.

### Catatan lingkungan

- File dibatasi di folder `workspace/`; path di luar itu ditolak.
- Agent sering dipakai di **Termux (Android)**: layar sempit, tidak ada `node`
  atau `npm`. Jangan berasumsi toolchain JS ada — cek dulu dengan `bash`.
  Untuk proyek Python, `python3 -m pytest` atau `unittest` biasanya paling aman.
