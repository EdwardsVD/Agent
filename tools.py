"""
tools.py
--------
Tool sandbox yang boleh dipanggil AI: read_file, write_file, edit_file, bash.
Sama seperti versi awal, semuanya dibatasi ke dalam SANDBOX_DIR biar aman.
"""

import os
import subprocess

SANDBOX_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "sandbox_workspace")
)
os.makedirs(SANDBOX_DIR, exist_ok=True)


def _safe_path(path: str) -> str:
    full = os.path.abspath(os.path.join(SANDBOX_DIR, path))
    if not full.startswith(SANDBOX_DIR):
        raise ValueError("Akses di luar sandbox ditolak")
    return full


def tool_read_file(args):
    try:
        with open(_safe_path(args["path"]), "r") as f:
            return f.read()
    except Exception as e:
        return f"[Error read_file: {e}]"


def tool_write_file(args):
    try:
        path = _safe_path(args["path"])
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(args["content"])
        return f"[OK] File ditulis: {args['path']}"
    except Exception as e:
        return f"[Error write_file: {e}]"


def tool_edit_file(args):
    try:
        path = _safe_path(args["path"])
        with open(path, "r") as f:
            content = f.read()
        if args["old"] not in content:
            return "[Error edit_file: teks 'old' tidak ditemukan di file]"
        if content.count(args["old"]) > 1:
            return "[Error edit_file: teks 'old' muncul lebih dari sekali, perjelas]"
        content = content.replace(args["old"], args["new"])
        with open(path, "w") as f:
            f.write(content)
        return f"[OK] File diedit: {args['path']}"
    except Exception as e:
        return f"[Error edit_file: {e}]"


def tool_bash(args, timeout=10):
    try:
        result = subprocess.run(
            args["command"],
            shell=True,
            cwd=SANDBOX_DIR,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        out = result.stdout + result.stderr
        return out.strip() or "[Tidak ada output]"
    except subprocess.TimeoutExpired:
        return "[Error: command timeout]"
    except Exception as e:
        return f"[Error bash: {e}]"


TOOLS = {
    "read_file": tool_read_file,
    "write_file": tool_write_file,
    "edit_file": tool_edit_file,
    "bash": tool_bash,
}
