#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test untuk fitur-fitur baru Agent v3.2.0:
- 24 Superpower Skills
- Code Generator & Templates (/template)
- Prompt Presets (/prompt)
- Termux & Android Storage Integration
- Zero-dependency HTTP requests shim
- Slash command handlers & Utilities
"""

import os
import sys
import unittest
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main  # noqa: E402


class TestV32SuperpowersSkills(unittest.TestCase):
    """Memastikan semua 24 skill Superpowers dimuat dengan benar."""

    def test_all_24_skills_loaded(self):
        skills = main.load_skills(force=True)
        self.assertGreaterEqual(len(skills), 24, "Harus memuat minimal 24 Superpower skills")

        expected_skills = [
            "brainstorming",
            "test-driven-development",
            "writing-plans",
            "systematic-debugging",
            "verification-before-completion",
            "using-superpowers",
            "prompt-to-project",
            "fullstack-code-generator",
            "api-design-and-scaffolding",
            "database-architect",
            "code-refactoring-and-clean-code",
            "frontend-ui-builder",
            "security-and-vulnerability-hardening",
            "scripting-and-automation",
            "bot-and-integrations-builder",
            "reverse-engineering-and-analysis",
        ]
        for sk in expected_skills:
            self.assertIn(sk, skills, f"Skill '{sk}' harus terdaftar")

    def test_new_skill_aliases_resolve(self):
        alias_checks = {
            "scaffold": "prompt-to-project",
            "p2p": "prompt-to-project",
            "fullstack": "fullstack-code-generator",
            "api": "api-design-and-scaffolding",
            "rest-api": "api-design-and-scaffolding",
            "database": "database-architect",
            "db": "database-architect",
            "refactor": "code-refactoring-and-clean-code",
            "frontend": "frontend-ui-builder",
            "ui": "frontend-ui-builder",
            "tailwind": "frontend-ui-builder",
            "security": "security-and-vulnerability-hardening",
            "automation": "scripting-and-automation",
            "scraper": "scripting-and-automation",
            "bot": "bot-and-integrations-builder",
            "telegram-bot": "bot-and-integrations-builder",
            "reverse": "reverse-engineering-and-analysis",
        }
        for alias, target in alias_checks.items():
            resolved = main.resolve_skill(alias)
            self.assertIsNotNone(resolved, f"Alias '{alias}' harusnya resolve")
            self.assertEqual(resolved["key"], target, f"Alias '{alias}' harus resolve ke '{target}'")


class TestTemplatesAndPresets(unittest.TestCase):
    """Test built-in templates dan prompt presets."""

    def test_builtin_templates_exist(self):
        for key in ("fastapi", "flask", "termux-tool", "sqlite-crud", "react-tailwind", "pytest-suite", "web-scraper", "telegram-bot"):
            self.assertIn(key, main.BUILTIN_TEMPLATES)
            tpl = main.BUILTIN_TEMPLATES[key]
            self.assertTrue(tpl["name"])
            self.assertTrue(tpl["files"])

    def test_handle_template_scaffolds_files(self):
        orig_ws = main.WORKSPACE_DIR
        with tempfile.TemporaryDirectory() as td:
            main.WORKSPACE_DIR = td
            try:
                main.handle_template("fastapi")
                self.assertTrue(os.path.isfile(os.path.join(td, "main.py")))
                self.assertTrue(os.path.isfile(os.path.join(td, "test_main.py")))
                self.assertTrue(os.path.isfile(os.path.join(td, "README.md")))
            finally:
                main.WORKSPACE_DIR = orig_ws

    def test_prompt_presets_valid(self):
        self.assertGreaterEqual(len(main.PROMPT_PRESETS), 8)
        for p in main.PROMPT_PRESETS:
            self.assertIn("id", p)
            self.assertIn("title", p)
            self.assertIn("prompt", p)
            self.assertIn("category", p)


class TestTermuxAndSystemUtilities(unittest.TestCase):
    """Test Termux helper, clipboard utils, dan model dynamic resolution."""

    def test_is_termux_callable(self):
        res = main.is_termux()
        self.assertIsInstance(res, bool)

    def test_phone_download_dir_callable(self):
        res = main.get_phone_download_dir()
        self.assertTrue(res is None or isinstance(res, str))

    def test_clipboard_helpers(self):
        # Clipboard get/set tidak boleh crash
        val = main.clipboard_get()
        self.assertIsInstance(val, str)
        # Testing set with empty or test text
        res = main.clipboard_set("test agent")
        self.assertIsInstance(res, bool)

    def test_dynamic_custom_model_resolution(self):
        m = main.find_model("ollama/deepseek-coder:latest")
        self.assertIsNotNone(m)
        self.assertEqual(m["id"], "ollama/deepseek-coder:latest")
        self.assertIn("Custom", m["label"])

    def test_version_is_v320(self):
        self.assertEqual(main.VERSION, "3.2.0")


class TestSnippetAndStats(unittest.TestCase):
    """Test snippet manager dan stats."""

    def test_stats_callable(self):
        state = main.State()
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            main.handle_stats(state)
        self.assertIn("Statistik Sesi", buf.getvalue())
        self.assertIn("v3.2.0", buf.getvalue())

    def test_snippet_list_callable(self):
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            main.handle_snippet("list")
        self.assertIn("Koleksi Snippet", buf.getvalue())


if __name__ == "__main__":
    unittest.main(verbosity=2)
