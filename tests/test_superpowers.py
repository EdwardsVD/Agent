#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test buat mesin Superpowers di main.py.

Jalanin:
    python3 -m unittest discover -s tests -v
atau:
    python3 tests/test_superpowers.py
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main  # noqa: E402


class TestSkillLibrary(unittest.TestCase):
    """Skill markdown dari obra/superpowers harus kebaca dari folder skills/."""

    def test_skills_folder_exists(self):
        self.assertTrue(
            os.path.isdir(main.SKILLS_DIR),
            f"folder skills/ harus ada di {main.SKILLS_DIR}",
        )

    def test_core_skills_loaded(self):
        skills = main.load_skills(force=True)
        for key in (
            "brainstorming",
            "test-driven-development",
            "writing-plans",
            "systematic-debugging",
            "verification-before-completion",
            "using-superpowers",
        ):
            self.assertIn(key, skills, f"skill inti '{key}' harus dimuat")

    def test_skill_has_description_and_body(self):
        sk = main.load_skills()["test-driven-development"]
        self.assertTrue(sk["description"], "frontmatter description harus keparsing")
        self.assertIn("NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST", sk["body"])

    def test_frontmatter_stripped_from_body(self):
        sk = main.load_skills()["brainstorming"]
        self.assertFalse(sk["body"].startswith("---"))

    def test_resources_discovered(self):
        sk = main.load_skills()["test-driven-development"]
        self.assertIn("writing-good-tests.md", sk["resources"])


class TestSkillResolution(unittest.TestCase):
    """Model harus bisa manggil skill pakai nama bebas."""

    def test_exact_name(self):
        self.assertEqual(main.resolve_skill("brainstorming")["key"], "brainstorming")

    def test_alias(self):
        self.assertEqual(main.resolve_skill("tdd")["key"], "test-driven-development")
        self.assertEqual(main.resolve_skill("debug")["key"], "systematic-debugging")

    def test_namespaced(self):
        self.assertEqual(main.resolve_skill("superpowers:tdd")["key"], "test-driven-development")

    def test_spaces_and_case(self):
        self.assertEqual(
            main.resolve_skill("Test Driven Development")["key"], "test-driven-development"
        )

    def test_unknown_returns_none(self):
        self.assertIsNone(main.resolve_skill("skill-yang-gak-ada-12345"))


class TestSkillTool(unittest.TestCase):
    def test_skill_tool_returns_body(self):
        out = main.tool_skill({"name": "tdd"}, {})
        self.assertIn("SKILL: test-driven-development", out)
        self.assertIn("NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST", out)

    def test_skill_tool_reads_resource(self):
        out = main.tool_skill(
            {"name": "tdd", "resource": "writing-good-tests.md"}, {}
        )
        self.assertIn("writing-good-tests.md", out)
        self.assertNotIn("[Error", out)

    def test_skill_tool_rejects_path_traversal(self):
        out = main.tool_skill({"name": "tdd", "resource": "../../main.py"}, {})
        self.assertIn("[Error", out)

    def test_unknown_skill_errors(self):
        self.assertIn("[Error", main.tool_skill({"name": "nggak-ada"}, {}))

    def test_list_skills(self):
        out = main.tool_list_skills({}, {})
        self.assertIn("brainstorming", out)
        self.assertIn("systematic-debugging", out)


class TestSystemPrompt(unittest.TestCase):
    def test_prompt_embeds_skill_index(self):
        p = main.build_system_prompt({"superpowers": True})
        self.assertIn("brainstorming", p)
        self.assertIn("test-driven-development", p)

    def test_prompt_embeds_bootstrap(self):
        p = main.build_system_prompt({"superpowers": True})
        self.assertIn("IF A SKILL APPLIES TO YOUR TASK", p)

    def test_prompt_has_iron_laws(self):
        p = main.build_system_prompt({"superpowers": True})
        self.assertIn("NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST", p)
        self.assertIn("NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE", p)
        self.assertIn("NO FIXES WITHOUT ROOT CAUSE FIRST", p)

    def test_lean_prompt_when_off(self):
        p = main.build_system_prompt({"superpowers": False})
        self.assertIn("Mode Superpowers OFF", p)
        self.assertNotIn("IF A SKILL APPLIES TO YOUR TASK", p)

    def test_prompt_lists_superpowers_tools(self):
        p = main.build_system_prompt({"superpowers": True})
        for tool in ("skill", "todo_write", "ask_user", "list_skills"):
            self.assertIn(tool, p)


class TestTestPathDetection(unittest.TestCase):
    def test_recognises_test_files(self):
        for p in (
            "tests/test_foo.py",
            "test_foo.py",
            "src/foo.test.js",
            "src/foo.spec.ts",
            "spec/foo_spec.rb",
            "__tests__/foo.js",
            "foo_test.go",
        ):
            self.assertTrue(main.TEST_PATH_RE.search(p), f"{p} harusnya dikenali test")

    def test_rejects_production_files(self):
        for p in ("src/app.py", "index.js", "lib/util.go", "main.py"):
            self.assertFalse(main.TEST_PATH_RE.search(p), f"{p} bukan file test")


class TestWorkflowLedger(unittest.TestCase):
    def setUp(self):
        self.wf = main.Workflow()

    def test_starts_empty(self):
        self.assertEqual(self.wf.summary()["skills"], [])
        self.assertEqual(self.wf.summary()["files"], 0)

    def test_records_skill(self):
        self.wf.note_skill("brainstorming")
        self.wf.note_skill("brainstorming")
        self.assertEqual(self.wf.skills, ["brainstorming"])

    def test_write_of_test_file_counts_as_test(self):
        self.wf.note_write("tests/test_a.py", 1)
        self.assertEqual(self.wf.tests, ["tests/test_a.py"])

    def test_write_of_prod_file_not_a_test(self):
        self.wf.note_write("src/a.py", 1)
        self.assertEqual(self.wf.tests, [])

    def test_successful_verify_command_recorded(self):
        self.wf.note_bash("python3 -m pytest tests/", "5 passed", 2)
        self.assertEqual(len(self.wf.verifications), 1)

    def test_failed_command_not_counted_as_evidence(self):
        self.wf.note_bash("python3 -m pytest", "boom\n[exit code: 1]", 2)
        self.assertEqual(self.wf.verifications, [])

    def test_non_verify_command_ignored(self):
        self.wf.note_bash("ls -la", "a\nb", 2)
        self.assertEqual(self.wf.verifications, [])

    def test_pending_verification_after_edit(self):
        self.wf.note_bash("python3 -m pytest", "ok", 1)
        self.assertFalse(self.wf.has_pending_verification())
        self.wf.note_write("src/a.py", 2)
        self.assertTrue(self.wf.has_pending_verification())
        self.wf.note_bash("python3 -m pytest", "ok", 3)
        self.assertFalse(self.wf.has_pending_verification())

    def test_gate_fires_only_up_to_limit(self):
        self.assertTrue(self.wf.can_fire("tdd"))
        self.assertFalse(self.wf.can_fire("tdd"))

    def test_reset_clears_everything(self):
        self.wf.note_skill("tdd")
        self.wf.note_write("a.py", 1)
        self.wf.reset()
        self.assertEqual(self.wf.skills, [])
        self.assertEqual(self.wf.writes, [])


class TestPreActionGate(unittest.TestCase):
    """Gate harus nge-block agent yang nyalip alur."""

    def setUp(self):
        self.wf = main.Workflow()
        self.cfg = {"superpowers": True, "gates": True}

    def test_blocks_write_without_any_skill(self):
        gate = main.pre_action_gate("write_file", {"path": "a.py"}, self.wf, self.cfg)
        self.assertIsNotNone(gate)
        self.assertIn("using-superpowers", gate)

    def test_blocks_write_without_approval(self):
        self.wf.note_skill("brainstorming")
        gate = main.pre_action_gate("write_file", {"path": "a.py"}, self.wf, self.cfg)
        self.assertIsNotNone(gate)
        self.assertIn("HARD-GATE", gate)

    def test_blocks_production_code_before_test(self):
        self.wf.note_skill("brainstorming")
        self.wf.note_approval("ok?", "ya")
        gate = main.pre_action_gate("write_file", {"path": "src/app.py"}, self.wf, self.cfg)
        self.assertIsNotNone(gate)
        self.assertIn("NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST", gate)

    def test_allows_writing_the_test_itself(self):
        self.wf.note_skill("tdd")
        self.wf.note_approval("ok?", "ya")
        gate = main.pre_action_gate(
            "write_file", {"path": "tests/test_app.py"}, self.wf, self.cfg
        )
        self.assertIsNone(gate)

    def test_allows_production_code_after_test_exists(self):
        self.wf.note_skill("tdd")
        self.wf.note_approval("ok?", "ya")
        self.wf.note_write("tests/test_app.py", 1)
        gate = main.pre_action_gate("write_file", {"path": "src/app.py"}, self.wf, self.cfg)
        self.assertIsNone(gate)

    def test_non_code_file_skips_tdd_gate(self):
        self.wf.note_skill("brainstorming")
        self.wf.note_approval("ok?", "ya")
        gate = main.pre_action_gate("write_file", {"path": "README.md"}, self.wf, self.cfg)
        self.assertIsNone(gate)

    def test_read_only_tools_never_blocked(self):
        for tool in ("read_file", "list_files", "grep_files", "bash", "web_search"):
            self.assertIsNone(
                main.pre_action_gate(tool, {"path": "x"}, main.Workflow(), self.cfg),
                f"{tool} gak boleh di-gate",
            )

    def test_gates_off_disables_blocking(self):
        cfg = {"superpowers": True, "gates": False}
        self.assertIsNone(main.pre_action_gate("write_file", {"path": "a.py"}, self.wf, cfg))

    def test_superpowers_off_disables_blocking(self):
        cfg = {"superpowers": False, "gates": True}
        self.assertIsNone(main.pre_action_gate("write_file", {"path": "a.py"}, self.wf, cfg))

    def test_gate_does_not_loop_forever(self):
        args = {"path": "a.py"}
        seen = set()
        for _ in range(12):
            g = main.pre_action_gate("write_file", args, self.wf, self.cfg)
            if g is None:
                break
            seen.add(g.splitlines()[0])
        self.assertIsNone(
            main.pre_action_gate("write_file", args, self.wf, self.cfg),
            "gate harus nyerah setelah batasnya, biar agent gak kejebak loop",
        )


class TestPreDoneGate(unittest.TestCase):
    def setUp(self):
        self.wf = main.Workflow()
        self.cfg = {"superpowers": True, "gates": True}

    def _fully_compliant(self):
        wf = main.Workflow()
        wf.note_skill("test-driven-development")
        wf.note_approval("ok?", "ya")
        wf.note_todos([{"task": "bikin fitur", "status": "done"}])
        wf.note_write("tests/test_a.py", 1)
        wf.note_write("src/a.py", 2)
        wf.note_bash("python3 -m pytest", "3 passed", 3)
        wf.note_read("src/a.py")
        return wf

    def test_blocks_done_without_skill(self):
        gate = main.pre_done_gate(self.wf, self.cfg)
        self.assertIsNotNone(gate)
        self.assertIn("using-superpowers", gate)

    def test_question_only_task_can_finish(self):
        self.wf.note_skill("brainstorming")
        self.assertIsNone(main.pre_done_gate(self.wf, self.cfg))

    def test_blocks_done_without_plan(self):
        self.wf.note_skill("tdd")
        self.wf.note_write("a.py", 1)
        gate = main.pre_done_gate(self.wf, self.cfg)
        self.assertIn("writing-plans", gate)

    def test_blocks_done_without_verification(self):
        wf = main.Workflow()
        wf.note_skill("tdd")
        wf.note_todos([{"task": "x", "status": "done"}])
        wf.note_write("a.py", 1)
        gate = main.pre_done_gate(wf, self.cfg)
        self.assertIn("NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE", gate)

    def test_blocks_done_when_edited_after_verifying(self):
        wf = main.Workflow()
        wf.note_skill("tdd")
        wf.note_todos([{"task": "x", "status": "done"}])
        wf.note_write("a.py", 1)
        wf.note_bash("python3 -m pytest", "ok", 2)
        wf.note_read("a.py")
        self.assertIsNone(main.pre_done_gate(wf, self.cfg))
        wf2 = self._fully_compliant()
        wf2.note_write("src/a.py", 9)  # diubah lagi sesudah verifikasi
        self.assertIn("verification-before-completion", main.pre_done_gate(wf2, self.cfg))

    def test_blocks_done_without_self_review(self):
        wf = main.Workflow()
        wf.note_skill("tdd")
        wf.note_todos([{"task": "x", "status": "done"}])
        wf.note_write("a.py", 1)
        wf.note_bash("python3 -m pytest", "ok", 2)
        gate = main.pre_done_gate(wf, self.cfg)
        self.assertIn("requesting-code-review", gate)

    def test_compliant_run_passes(self):
        self.assertIsNone(main.pre_done_gate(self._fully_compliant(), self.cfg))

    def test_gates_off_allows_done(self):
        self.assertIsNone(main.pre_done_gate(self.wf, {"superpowers": True, "gates": False}))


class TestAntiGaming(unittest.TestCase):
    """Agent gak boleh bisa ngakalin gate dengan trik murahan."""

    def setUp(self):
        self.wf = main.Workflow()
        self.cfg = {"superpowers": True, "gates": True}

    def test_version_check_is_not_evidence(self):
        for cmd in ("python3 --version", "node -v", "npm --version", "go version"):
            wf = main.Workflow()
            wf.note_bash(cmd, "v1.2.3", 1)
            self.assertEqual(wf.verifications, [], f"'{cmd}' bukan bukti verifikasi")

    def test_trivial_commands_are_not_evidence(self):
        for cmd in ("echo ok", "true", "ls tests/", "pwd", "cat file.py", "touch x"):
            wf = main.Workflow()
            wf.note_bash(cmd, "output", 1)
            self.assertEqual(wf.verifications, [], f"'{cmd}' bukan bukti verifikasi")

    def test_real_test_run_is_evidence(self):
        for cmd in ("python3 -m pytest", "npm test", "python3 test_calc.py",
                    "node --check app.js", "python3 -m py_compile a.py"):
            wf = main.Workflow()
            wf.note_bash(cmd, "ok", 1)
            self.assertTrue(wf.verifications, f"'{cmd}' harusnya dihitung bukti")

    def test_empty_test_file_does_not_satisfy_tdd_gate(self):
        self.wf.note_skill("tdd")
        self.wf.note_approval("q", "ya")
        self.wf.note_write("tests/test_a.py", 1, content="")
        self.assertEqual(self.wf.tests, [], "file test kosong gak boleh ngitung")
        gate = main.pre_action_gate("write_file", {"path": "src/a.py"}, self.wf, self.cfg)
        self.assertIsNotNone(gate)

    def test_stub_test_file_does_not_satisfy_tdd_gate(self):
        self.wf.note_skill("tdd")
        self.wf.note_approval("q", "ya")
        self.wf.note_write("tests/test_a.py", 1, content="def test_a():\n    pass\n")
        self.assertEqual(self.wf.tests, [])

    def test_real_test_file_satisfies_tdd_gate(self):
        self.wf.note_skill("tdd")
        self.wf.note_approval("q", "ya")
        self.wf.note_write(
            "tests/test_a.py", 1,
            content="from a import add\n\ndef test_add():\n    assert add(2, 3) == 5\n",
        )
        self.assertEqual(self.wf.tests, ["tests/test_a.py"])
        self.assertIsNone(
            main.pre_action_gate("write_file", {"path": "src/a.py"}, self.wf, self.cfg)
        )

    def test_js_test_with_expect_counts(self):
        self.wf.note_write(
            "src/a.test.js", 1,
            content="test('adds', () => { expect(add(1,2)).toBe(3); });",
        )
        self.assertEqual(self.wf.tests, ["src/a.test.js"])


class TestTermuxFriendliness(unittest.TestCase):
    """Harus waras di HP: layar sempit, path aneh, folder salah."""

    def test_narrow_terminal_not_forced_wide(self):
        import shutil as _sh
        real = _sh.get_terminal_size
        try:
            _sh.get_terminal_size = lambda *a, **k: os.terminal_size((32, 24))
            self.assertLessEqual(main.term_width(), 32,
                                 "layar HP 32 kolom gak boleh dipaksa jadi 50")
            self.assertTrue(main.is_narrow())
        finally:
            _sh.get_terminal_size = real

    def test_wide_terminal_capped(self):
        import shutil as _sh
        real = _sh.get_terminal_size
        try:
            _sh.get_terminal_size = lambda *a, **k: os.terminal_size((400, 24))
            self.assertLessEqual(main.term_width(), 100)
            self.assertFalse(main.is_narrow())
        finally:
            _sh.get_terminal_size = real

    def test_zero_width_falls_back(self):
        import shutil as _sh
        real = _sh.get_terminal_size
        try:
            _sh.get_terminal_size = lambda *a, **k: os.terminal_size((0, 0))
            self.assertEqual(main.term_width(), 78)
        finally:
            _sh.get_terminal_size = real

    def test_panels_render_on_narrow_screen(self):
        import shutil as _sh, io, contextlib
        real = _sh.get_terminal_size
        try:
            _sh.get_terminal_size = lambda *a, **k: os.terminal_size((30, 24))
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                main.todo_panel([{"task": "task panjang banget " * 5, "status": "done"}])
                main.gate_line("GATE [x] — tes\n" + "kalimat panjang " * 10)
                main.question_panel("pertanyaan panjang " * 6, ["ya", "tidak"])
            self.assertTrue(buf.getvalue().strip(), "panel harus tetap ngeluarin sesuatu")
        finally:
            _sh.get_terminal_size = real

    def test_finds_real_agent_dir_from_empty_nested_folder(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            real = os.path.join(td, "Agent")
            os.makedirs(os.path.join(real, "skills"))
            open(os.path.join(real, "main.py"), "w").close()
            trap = os.path.join(real, "Agent")   # folder kosong hasil clone gagal
            os.makedirs(trap)
            found = main._find_real_agent_dir(trap)
            self.assertEqual(os.path.abspath(found), os.path.abspath(real))

    def test_find_returns_none_when_nothing_around(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            self.assertIsNone(main._find_real_agent_dir(td))

    def test_doctor_passes_on_healthy_install(self):
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            ok = main.doctor(verbose=True)
        self.assertTrue(ok, "instalasi repo ini harusnya sehat")
        self.assertIn("Agent Doctor", buf.getvalue())

    def test_doctor_quiet_mode_returns_bool(self):
        self.assertIsInstance(main.doctor(verbose=False), bool)


class TestHarnessReference(unittest.TestCase):
    """Adaptasi harness: skill subagent gak boleh dipakai mentah-mentah."""

    def test_agent_cli_reference_exists(self):
        sk = main.load_skills(force=True)["using-superpowers"]
        self.assertIn("references/agent-cli-tools.md", sk["resources"])

    def test_reference_readable_via_skill_tool(self):
        out = main.tool_skill(
            {"name": "using-superpowers", "resource": "references/agent-cli-tools.md"}, {}
        )
        self.assertNotIn("[Error", out)
        self.assertIn("subagent", out.lower())

    def test_prompt_warns_about_subagents(self):
        p = main.build_system_prompt({"superpowers": True})
        self.assertIn("agent-cli-tools.md", p)

    def test_prompt_has_no_stray_double_braces(self):
        p = main.build_system_prompt({"superpowers": True})
        self.assertNotIn('{{"name"', p, "sisa escaping .format() yang bikin JSON salah")
        self.assertIn('{"name": "brainstorming"}', p)


class TestGracefulDegradation(unittest.TestCase):
    """Kalau user cuma nyalin main.py tanpa folder skills/, agent harus tetap
    jalan — bukan kejebak gate yang mustahil dipenuhi."""

    def setUp(self):
        self._real_dir = main.SKILLS_DIR
        main.SKILLS_DIR = os.path.join(os.path.dirname(self._real_dir), "_skills_gak_ada_")
        main.load_skills(force=True)

    def tearDown(self):
        main.SKILLS_DIR = self._real_dir
        main.load_skills(force=True)

    def test_no_skills_loaded(self):
        self.assertEqual(main.load_skills(), {})

    def test_gates_disabled_without_skills(self):
        cfg = {"superpowers": True, "gates": True}
        self.assertIsNone(
            main.pre_action_gate("write_file", {"path": "a.py"}, main.Workflow(), cfg),
            "gate 'invoke skill' mustahil dipenuhi kalau gak ada skill — harus mati",
        )
        self.assertIsNone(main.pre_done_gate(main.Workflow(), cfg))

    def test_falls_back_to_lean_prompt(self):
        p = main.build_system_prompt({"superpowers": True})
        self.assertIn("Mode Superpowers OFF", p)

    def test_skill_tool_gives_helpful_error(self):
        out = main.tool_list_skills({}, {})
        self.assertIn("[Error", out)
        self.assertIn("git clone", out)


class TestTodoTool(unittest.TestCase):
    def test_accepts_dicts(self):
        out = main.tool_todo_write(
            {"todos": [{"task": "a", "status": "done"}, {"task": "b", "status": "pending"}]}, {}
        )
        self.assertIn("1/2 beres", out)

    def test_accepts_plain_strings(self):
        out = main.tool_todo_write({"todos": ["a", "b"]}, {})
        self.assertIn("0/2 beres", out)

    def test_normalises_status_synonyms(self):
        todos = main._normalize_todos([{"task": "a", "status": "selesai"},
                                       {"task": "b", "status": "in progress"}])
        self.assertEqual(todos[0]["status"], "done")
        self.assertEqual(todos[1]["status"], "in_progress")

    def test_empty_errors(self):
        self.assertIn("[Error", main.tool_todo_write({"todos": []}, {}))

    def test_updates_global_workflow(self):
        main.WORKFLOW.reset()
        main.tool_todo_write({"todos": ["x"]}, {})
        self.assertEqual(len(main.WORKFLOW.todos), 1)


class TestWorkflowRecord(unittest.TestCase):
    def setUp(self):
        self.wf = main.Workflow()

    def test_records_skill_invocation(self):
        main.workflow_record("skill", {"name": "tdd"}, "…", self.wf, 1)
        self.assertIn("test-driven-development", self.wf.skills)

    def test_records_write(self):
        main.workflow_record("write_file", {"path": "a.py"}, "[OK] File ditulis", self.wf, 1)
        self.assertIn("a.py", self.wf.writes)

    def test_failed_write_not_recorded(self):
        main.workflow_record("write_file", {"path": "a.py"}, "[Error write_file: nope]", self.wf, 1)
        self.assertEqual(self.wf.writes, [])

    def test_records_verification(self):
        main.workflow_record("bash", {"command": "python3 -m pytest"}, "2 passed", self.wf, 1)
        self.assertEqual(len(self.wf.verifications), 1)

    def test_records_review_read(self):
        main.workflow_record("read_file", {"path": "a.py"}, "isi", self.wf, 1)
        self.assertEqual(self.wf.reviews, 1)


class TestToolRegistry(unittest.TestCase):
    def test_superpowers_tools_registered(self):
        for name in ("skill", "list_skills", "todo_write", "ask_user"):
            self.assertIn(name, main.TOOLS)

    def test_original_tools_still_there(self):
        for name in ("list_files", "grep_files", "read_file", "write_file",
                     "edit_file", "bash", "web_search", "web_fetch"):
            self.assertIn(name, main.TOOLS)

    def test_every_prompt_tool_exists(self):
        prompt = main.build_system_prompt({"superpowers": True})
        for name in main.TOOLS:
            self.assertIn(name, prompt, f"tool {name} harus disebut di system prompt")


class TestParseResponseStillWorks(unittest.TestCase):
    """Regression: parser lama gak boleh rusak gara-gara tool baru."""

    def test_parses_skill_action(self):
        p = main.parse_response('THINK: cek skill\n\nACTION: skill\nINPUT: {"name": "brainstorming"}')
        self.assertEqual(p["kind"], "action")
        self.assertEqual(p["tool"], "skill")
        self.assertEqual(p["args"]["name"], "brainstorming")

    def test_parses_done(self):
        self.assertEqual(main.parse_response("DONE: beres")["kind"], "done")

    def test_parses_todo_write_with_list(self):
        p = main.parse_response(
            'ACTION: todo_write\nINPUT: {"todos": [{"task": "a", "status": "pending"}]}'
        )
        self.assertEqual(p["tool"], "todo_write")
        self.assertEqual(len(p["args"]["todos"]), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
