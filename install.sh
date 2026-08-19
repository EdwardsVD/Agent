#!/usr/bin/env bash
# ============================================================================
# Agent CLI — One-Click Setup & Installer for Termux, Linux & macOS
# ============================================================================
#
# Cara pakai di Termux / Linux:
#   bash install.sh
# Atau:
#   ./install.sh
#
# Installer ini otomatis:
# 1. Mengecek & memasang dependencies (Python, Git, Pip)
# 2. Mengkonfigurasi penyimpanan Termux (termux-setup-storage)
# 3. Menginstall modul Python yang dibutuhkan
# 4. Membuat perintah global 'agent' agar bisa dijalankan dari mana saja
# 5. Menjalankan diagnosis kesehatan sistem (Agent Doctor)
# ============================================================================

set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "========================================================="
echo "   [SUPERPOWERS] AGENT CLI — SUPERPOWERS INSTALLER v3.2.0"
echo "========================================================="
echo "[DIR] Direktori : $DIR"

IS_TERMUX=false
if [ -d "/data/data/com.termux" ] || [ -n "${TERMUX_VERSION:-}" ]; then
    IS_TERMUX=true
    echo "[TERMUX] Terdeteksi: Lingkungan ANDROID TERMUX"
else
    echo "[BASH] Terdeteksi: Lingkungan Linux / macOS / Unix"
fi
echo

# ----------------------------------------------------------------------------
# 1. Pemasangan Package Dasar (khusus Termux)
# ----------------------------------------------------------------------------
if [ "$IS_TERMUX" = true ]; then
    echo " [1/5] Memeriksa paket Termux (python, git, termux-api)..."
    if ! command -v python3 >/dev/null 2>&1 && ! command -v python >/dev/null 2>&1; then
        echo "   Menginstall python..."
        pkg install python -y || apt-get install python -y
    fi
    if ! command -v git >/dev/null 2>&1; then
        echo "   Menginstall git..."
        pkg install git -y || apt-get install git -y
    fi
    if ! command -v termux-notification >/dev/null 2>&1; then
        echo "   Menginstall termux-api (opsional untuk notifikasi & clipboard)..."
        pkg install termux-api -y 2>/dev/null || true
    fi
    
    # Cek permission storage Termux
    if [ ! -d "$HOME/storage" ] && [ ! -d "/sdcard" ]; then
        echo "[TERMUX] Ingin mengaktifkan akses memori HP (agar file zip bisa langsung ke Download)?"
        echo "   Menjalankan termux-setup-storage..."
        termux-setup-storage 2>/dev/null || true
    fi
fi

# ----------------------------------------------------------------------------
# 2. Deteksi Python Interpreter
# ----------------------------------------------------------------------------
echo "[PYTHON] [2/5] Mencari Python..."
PY=""
for c in python3 python python3.12 python3.11 python3.10 python3.9; do
    if command -v "$c" >/dev/null 2>&1; then
        PY="$c"
        break
    fi
done

if [ -z "$PY" ]; then
    echo "[X] Error: Python tidak ditemukan!"
    if [ "$IS_TERMUX" = true ]; then
        echo "  Jalankan: pkg install python -y"
    else
        echo "  Pasang Python 3.8+ melalui package manager distro Anda."
    fi
    exit 1
fi
echo "[OK] Python aktif: $($PY --version 2>&1) ($PY)"

# ----------------------------------------------------------------------------
# 3. Install Python Dependencies
# ----------------------------------------------------------------------------
echo " [3/5] Memeriksa dependensi Python..."
if [ -f requirements.txt ]; then
    $PY -m pip install -q --break-system-packages -r requirements.txt 2>/dev/null \
        || $PY -m pip install -q -r requirements.txt 2>/dev/null \
        || pip install -q -r requirements.txt 2>/dev/null \
        || echo "[WARN] Catatan: Pip install dilewati, Agent memiliki built-in fallback zero-dependency."
fi

# ----------------------------------------------------------------------------
# 4. Beri Permission Eksekusi & Buat Shortcut Global 'agent'
# ----------------------------------------------------------------------------
echo "[CONFIG] [4/5] Membuat shortcut global 'agent'..."
chmod +x "$DIR/run.sh" 2>/dev/null || true
chmod +x "$DIR/main.py" 2>/dev/null || true
chmod +x "$DIR/install.sh" 2>/dev/null || true

# Buat launcher script di bin jika memungkinkan
BIN_DIR=""
if [ -d "/data/data/com.termux/files/usr/bin" ] && [ -w "/data/data/com.termux/files/usr/bin" ]; then
    BIN_DIR="/data/data/com.termux/files/usr/bin"
elif [ -d "$HOME/bin" ]; then
    BIN_DIR="$HOME/bin"
elif [ -d "$HOME/.local/bin" ]; then
    BIN_DIR="$HOME/.local/bin"
fi

if [ -n "$BIN_DIR" ]; then
    mkdir -p "$BIN_DIR"
    cat <<EOF > "$BIN_DIR/agent"
#!/usr/bin/env bash
exec bash "$DIR/run.sh" "\$@"
EOF
    chmod +x "$BIN_DIR/agent"
    echo "[OK] Perintah 'agent' dipasang di $BIN_DIR/agent"
fi

# Tambahkan alias ke .bashrc dan .zshrc
for RC in "$HOME/.bashrc" "$HOME/.zshrc"; do
    if [ -f "$RC" ] || [ -f "$HOME/.bash_profile" ]; then
        TARGET="${RC}"
        [ ! -f "$TARGET" ] && TARGET="$HOME/.bash_profile"
        if ! grep -q "alias agent=" "$TARGET" 2>/dev/null; then
            echo "" >> "$TARGET"
            echo "# Agent CLI shortcut" >> "$TARGET"
            echo "alias agent='bash \"$DIR/run.sh\"'" >> "$TARGET"
            echo "[OK] Alias 'agent' ditambahkan ke $TARGET"
        fi
    fi
done

# ----------------------------------------------------------------------------
# 5. Verifikasi Instalasi dengan Agent Doctor
# ----------------------------------------------------------------------------
echo "[DOCTOR] [5/5] Memeriksa kesehatan instalasi..."
echo
$PY main.py --doctor || true

echo "========================================================="
echo "[SUCCESS] INSTALASI SELESAI!"
echo "========================================================="
echo "Cara menjalankan Agent:"
echo "  1. Dari folder ini   : bash run.sh  (atau: python3 main.py)"
echo "  2. Dari mana saja    : agent"
echo
echo "Ketik /help di dalam Agent untuk melihat 24 skill Superpowers,"
echo "template generator (/template), prompt presets (/prompt), dan fitur lainnya."
echo "========================================================="
