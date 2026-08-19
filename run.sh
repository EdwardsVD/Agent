#!/usr/bin/env bash
# ============================================================================
# Agent CLI — Launcher Anti-Gagal untuk Termux / Android / Linux / macOS
# ============================================================================
#
#   bash run.sh [argumen]
#
# Mengatasi semua kendala umum di Termux:
# - Selalu berpindah ke direktori skrip yang benar (mencegah error Agent/Agent)
# - Menemukan interpreter Python secara otomatis
# - Menangani instalasi requests secara aman dengan --break-system-packages
# - Mendukung fallback zero-dependency jika pip tidak tersedia
# - Terintegrasi dengan storage Android & clipboard
# ============================================================================

set -u

# Pindah ke folder script ini — ini yang bikin masalah Agent/Agent gak kejadian.
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR" || exit 1

# Cari interpreter Python: Termux kadang cuma punya 'python' atau 'python3'.
PY=""
for c in python3 python python3.12 python3.11 python3.10 python3.9; do
  if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
done

if [ -z "$PY" ]; then
  echo "✖ Python gak ketemu."
  if [ -d "/data/data/com.termux" ] || [ -n "${TERMUX_VERSION:-}" ]; then
    echo "  Di Termux jalanin: pkg install python -y"
  else
    echo "  Pasang Python 3.8+ di sistem kamu."
  fi
  exit 1
fi

if [ ! -f main.py ]; then
  echo "✖ main.py gak ketemu di $DIR. Instalasi kamu rusak."
  echo "  Benerin dengan:"
  echo "    cd ~ && rm -rf Agent"
  echo "    git clone https://github.com/EdwardsVD/Agent.git"
  echo "    cd Agent && bash run.sh"
  exit 1
fi

# Cek apakah modul requests ada; kalau belum, coba install otomatis tapi jangan crash kalau pip gagal.
if ! $PY -c "import requests" >/dev/null 2>&1; then
  echo "📦 Memeriksa dependensi (requests)..."
  $PY -m pip install -q --break-system-packages -r requirements.txt 2>/dev/null \
    || $PY -m pip install -q -r requirements.txt 2>/dev/null \
    || pip install -q -r requirements.txt 2>/dev/null \
    || true
fi

# Peringatan kalau folder skills/ gak ikut ke-clone.
if [ ! -d skills ]; then
  echo "⚠ Folder skills/ gak ada — Superpowers bakal MATI (mode polos)."
  echo "  Clone repo-nya lengkap biar dapet 24 skill Superpowers."
fi

# Eksekusi main.py dengan semua argumen yang diteruskan
exec $PY main.py "$@"
