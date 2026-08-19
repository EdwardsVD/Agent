---
name: scripting-and-automation
description: "Use when writing automation scripts, web scrapers, data pipelines, CLI tools, cron jobs, or Termux mobile automation scripts."
---

# Scripting & Automation Superpower

Create robust, self-healing, efficient automation scripts and CLI utilities for Linux, macOS, and Termux environments.

## Scripting Principles

1. **Bash Scripts**:
   - Always use `set -euo pipefail` to catch errors early.
   - Use meaningful variable names with quotes: `"${VAR}"`.
   - Provide clear `--help` output and informative colored logs.
2. **Python Automation**:
   - Use `argparse` or `click` for powerful CLI interfaces.
   - Use `logging` or styled console outputs.
   - Implement exponential backoff retry logic for network calls.
3. **Termux Mobile Automation**:
   - Integrate with `termux-api` commands when present (`termux-battery-status`, `termux-vibrate`, `termux-toast`, `termux-clipboard-set/get`).
   - Support low-memory usage and intermittent connectivity gracefully.
4. **Scraping & Data Processing**:
   - Include custom headers (`User-Agent`) and respect rate limits.
   - Output structured formats (JSON / CSV / SQLite).

## Resource Reference

Read `automation-recipes.md` for CLI argument parsing and Termux hooks:
`ACTION: skill INPUT: {"name": "scripting-and-automation", "resource": "automation-recipes.md"}`
