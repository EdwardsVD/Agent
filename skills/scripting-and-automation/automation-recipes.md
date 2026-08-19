# Automation & CLI Recipes

## Python Termux & Linux CLI Template
```python
#!/usr/bin/env python3
import sys
import os
import argparse
import subprocess

def check_termux_battery():
    if shutil.which("termux-battery-status"):
        res = subprocess.run(["termux-battery-status"], capture_output=True, text=True)
        return res.stdout
    return "Not in Termux or termux-api not installed"

def main():
    parser = argparse.ArgumentParser(description="Automated Tool")
    parser.add_argument("--input", "-i", required=True, help="Input path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose mode")
    args = parser.parse_args()
    print(f"Processing {args.input}...")

if __name__ == "__main__":
    main()
```
