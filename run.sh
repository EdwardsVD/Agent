#!/usr/bin/env bash
# Agent CLI — launcher anti-gagal buat Termux / Linux / macOS.
#
#   bash run.sh
#
# Kenapa ada file ini? Karena error paling sering di Termux itu:
#   python: can't open file '/data/data/.../home/Agent/Agent/main.py'
# gara-gara kejebak di folder Agent/Agent yang kosong (clone gagal/keinterupsi).
# Script ini selalu pindah ke folder tempat dirinya sendiri berada, jadi
# kamu boleh jalanin dari mana aja.

set -u

# Pindah ke folder script ini — ini yang bikin masalah Agent/Agent gak kejadian.
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)" || exit 1

echo "📂 Folder Agent : $(pwd)"

if [ ! -f main.py ]; then
  echo "✖ main.py gak ketemu di sini. Instalasi kamu rusak."
  echo "  Benerin dengan:"
  echo "    cd ~ && rm -rf Agent"
  echo "    git clone https://github.com/EdwardsVD/Agent.git"
  echo "    cd Agent && bash run.sh"
  exit 1
fi

# Cari interpreter Python: Termux kadang cuma punya 'python'.
PY=""
for c in python3 python python3.12 python3.11 python3.10 python3.9; do
  if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
done

if [ -z "$PY" ]; then
  echo "✖ Python gak ketemu."
  echo "  Di Termux jalanin: pkg install python -y"
  exit 1
fi

echo "🐍 Python       : $($PY --version 2>&1)"

# Pastikan requests ada; kalau belum, install otomatis.
if ! $PY -c "import requests" >/dev/null 2>&1; then
  echo "📦 Modul 'requests' belum ada — nginstall dulu…"
  $PY -m pip install -q -r requirements.txt 2>/dev/null \
    || $PY -m pip install -q --break-system-packages -r requirements.txt 2>/dev/null \
    || pip install -q -r requirements.txt 2>/dev/null
  if ! $PY -c "import requests" >/dev/null 2>&1; then
    echo "✖ Gagal nginstall 'requests'. Coba manual:"
    echo "    $PY -m pip install requests"
    exit 1
  fi
  echo "✔ requests keinstall."
fi

# Peringatan kalau folder skills/ gak ikut ke-clone.
if [ ! -d skills ]; then
  echo "⚠ Folder skills/ gak ada — Superpowers bakal MATI (mode polos)."
  echo "  Clone repo-nya lengkap biar dapet skill-nya."
fi

echo "🚀 Jalanin Agent…"
echo
exec $PY main.py "$@"
