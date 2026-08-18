# NOTICE — Asal-usul skill di folder ini

Isi folder `skills/` ini di-**vendor** (disalin apa adanya) dari proyek
**Superpowers** karya Jesse Vincent:

- Sumber : https://github.com/obra/superpowers
- Lisensi: MIT License — Copyright (c) 2025 Jesse Vincent
- Versi  : superpowers v6.3.0
- Commit : b36e0829c6d0140e93cfef2ca599b1b07d4a7797

## Kenapa di-vendor, bukan di-download pas jalan?

Biar `git clone` + `python main.py` langsung jalan di **Termux / HP** tanpa
internet dan tanpa `npm`. Skill dibaca langsung dari disk.

## Yang disalin

**Semua file markdown** dari `skills/` upstream (SKILL.md + seluruh resource
pendukungnya: `references/`, `examples/`, prompt reviewer, best-practices, dll),
plus resource non-markdown yang dirujuk langsung oleh skill:

- `systematic-debugging/condition-based-waiting-example.ts`
- `systematic-debugging/find-polluter.sh`
- `writing-skills/graphviz-conventions.dot`

Total 42 file dari upstream. Yang **tidak** ikut cuma script khusus harness lain
yang gak ada gunanya di sini (`brainstorming/scripts/*` buat visual companion
berbasis Node, `subagent-driven-development/scripts/*` buat dispatch subagent,
dan `writing-skills/render-graphs.js`) — harness Python ini gak punya
Node/subagent, dan Termux biasanya gak ada `npm`.

## Tambahan dari repo ini (bukan dari upstream)

- `using-superpowers/references/agent-cli-tools.md` — ditulis khusus buat harness
  ini, ngikutin pola `references/<harness>-tools.md` punya upstream. Isinya
  pemetaan tool + peringatan bahwa `subagent-driven-development` dan
  `dispatching-parallel-agents` **gak bisa dipakai mentah-mentah** di sini
  (harness ini belum punya subagent), plus daftar workflow gate yang dipaksa
  di level kode.

## Perubahan

Isi skill upstream **tidak diubah sama sekali**. Maintainer Superpowers
menegaskan bahwa konten skill itu sudah di-tuning lewat eval, jadi kata-katanya
dibiarkan utuh. Yang ditulis dari nol di repo ini cuma *harness*-nya: loader
skill, tool `skill`, dan workflow gate di `main.py`.

## Update skill

```bash
git clone --depth 1 https://github.com/obra/superpowers.git /tmp/superpowers
cd /tmp/superpowers/skills
find . -name "*.md" -exec cp --parents {} /path/ke/Agent/skills/ \;
```

Lalu jalankan `/superpowers reload` di dalam Agent CLI, atau restart programnya.
Jangan lupa file ini dan `agent-cli-tools.md` jangan ketimpa.

---

Teks lengkap lisensi MIT dari proyek Superpowers ada di `LICENSE-superpowers.txt`.
