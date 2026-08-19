---
name: prompt-to-project
description: "Use when user gives a broad, brief, or open-ended request to generate code or projects from scratch. Scaffolds complete, production-ready architecture with clean files, dependencies, tests, and documentation."
---

# Prompt to Project: Zero-to-One Instant Code Scaffolding

Transform ambiguous, concise, or broad user prompts into complete, well-architected, and fully functional codebases.

## Overview

When a user asks to build "anything" (e.g. "bikin web e-commerce", "bikin bot telegram", "bikin script backup", "bikin REST API CRUD"), do not produce half-baked or placeholder snippets. Follow this disciplined blueprint:

1. **Clarify & Classify Intent**: Identify the domain (Web, Backend, CLI, Bot, Mobile/Termux, Data).
2. **Architecture Blueprint**: Define directory structure, core entry points, configuration, and dependencies.
3. **Interactive Confirmation**: Present the chosen stack and structure to the human partner using `ask_user`.
4. **Step-by-Step Generation**: Use `todo_write` to track progress and generate files in logical order:
   - Config / Environment (`.env.example`, `requirements.txt` / `package.json`)
   - Core domain logic / models
   - Business handlers / controllers / routes
   - Tests (`tests/test_*.py` or test files)
   - Entry point (`main.py`, `app.py`, `index.js`, or CLI runner)
   - Documentation (`README.md`)
5. **Fresh Verification**: Run syntax checks and test suites (`python3 -m unittest`, `pytest`, `node --check`) before reporting completion.

## Golden Rules for Generation

- **No Placeholders**: Never write `# TODO: implement later` for core logic. Write working, functional code.
- **Self-Contained & Runnable**: Every generated project must run without mysterious missing imports.
- **Safe Defaults**: Use lightweight, reliable dependencies that work smoothly across Linux, Termux, and macOS.
- **Zero-Config Run**: Include clear run commands in the `README.md` or a `run.sh` script.

## Resource Reference

Read `scaffolding-templates.md` for standard directory layouts across Python, Node.js, and Bash:
`ACTION: skill INPUT: {"name": "prompt-to-project", "resource": "scaffolding-templates.md"}`
