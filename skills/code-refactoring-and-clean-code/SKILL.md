---
name: code-refactoring-and-clean-code
description: "Use when modernizing, restructuring, optimizing, or cleaning up existing code without altering behavior. Implements SOLID principles and design patterns."
---

# Code Refactoring & Clean Code Superpower

Transform messy, legacy, or complex code into clean, modular, and maintainable software while preserving exact behavior.

## Core Rules

1. **Verify Baseline First**: Run existing tests before making any changes. If tests don't exist, write tests FIRST (TDD).
2. **Small Incremental Steps**: Refactor one function/module at a time; verify after each step.
3. **SOLID Principles**:
   - Single Responsibility: Each function/class does one thing well.
   - Open/Closed: Easily extendable without modifying core interfaces.
   - Dependency Inversion: Inject dependencies rather than hardcoding them.
4. **Code Smells to Eliminate**:
   - Long functions (> 40 lines) -> Extract helper methods.
   - Deep nested conditionals (> 3 levels) -> Guard clauses & early returns.
   - Magic numbers/strings -> Named constants.
   - Duplicate code (DRY) -> Shared utilities.
5. **Modern Type Hints & Docstrings**:
   - Add Python 3.9+ type hints (`def process(items: list[str]) -> dict[str, int]:`).
   - Add concise Google/Numpy/Sphinx style docstrings.

## Resource Reference

Read `refactoring-checklist.md`:
`ACTION: skill INPUT: {"name": "code-refactoring-and-clean-code", "resource": "refactoring-checklist.md"}`
