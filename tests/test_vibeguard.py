import io
import json
import os
import re
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import vibeguard as vg  # noqa: E402


def write_lines(path, count):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("".join("x = %d\n" % i for i in range(count)))


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


class Base(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir)

    def p(self, *parts):
        return os.path.join(self.dir, *parts)

    def run_main(self, *argv, stdin=None):
        out, err = io.StringIO(), io.StringIO()
        code = vg.main(list(argv), stdin=stdin, out=out, err=err)
        return code, out.getvalue(), err.getvalue()


class CountLines(Base):
    def test_counts_with_and_without_final_newline(self):
        cases = [(b"", 0), (b"a\n", 1), (b"a\nb", 2), (b"a\r\nb\r\n", 2), (b"\n\n", 2)]
        for data, want in cases:
            with open(self.p("f.py"), "wb") as f:
                f.write(data)
            self.assertEqual(vg.count_lines(self.p("f.py")), want, data)


class Check(Base):
    def test_800_lines_is_ok(self):
        write_lines(self.p("src", "a.py"), 800)
        code, out, _ = self.run_main("check", self.dir)
        self.assertEqual(code, 0, out)
        self.assertIn("OK", out)

    def test_split_and_over_longest_first(self):
        write_lines(self.p("src", "big.rs"), 801)
        write_lines(self.p("main.ts"), 1001)
        code, out, _ = self.run_main("check", self.dir)
        self.assertEqual(code, 1)
        self.assertRegex(out, r"SPLIT\s+801\s+\S*src/big\.rs")
        self.assertRegex(out, r"OVER\s+1001\s+\S*main\.ts")
        self.assertLess(out.index("main.ts"), out.index("big.rs"))

    def test_ignores_vendor_hidden_generated_and_non_code(self):
        for parts in [("node_modules", "x.js"), (".git", "x.py"), ("target", "x.rs"),
                      ("notes.md",), ("data.txt",), ("app.min.js",)]:
            write_lines(self.p(*parts), 2000)
        code, out, _ = self.run_main("check", self.dir)
        self.assertEqual(code, 0, out)

    def test_memory_bank_notes_are_counted(self):
        write_lines(self.p("memory-bank", "log.md"), 900)
        code, out, _ = self.run_main("check", self.dir)
        self.assertEqual(code, 1)
        self.assertIn("memory-bank/log.md", out)

    def test_explicit_file_is_always_checked(self):
        write_lines(self.p("notes.txt"), 900)
        code, out, _ = self.run_main("check", self.p("notes.txt"))
        self.assertEqual(code, 1, out)

    def test_missing_path_is_an_error(self):
        code, _, err = self.run_main("check", self.p("nope"))
        self.assertEqual(code, 2)
        self.assertIn("not found", err)


class Init(Base):
    def test_creates_the_project_files(self):
        code, out, _ = self.run_main("init", self.dir)
        self.assertEqual(code, 0, out)
        for rel in vg.PROJECT_FILES + ("CLAUDE.md",):
            self.assertTrue(os.path.isfile(self.p(*rel.split("/"))), rel)
        with open(self.p("CLAUDE.md"), "rb") as f:
            self.assertEqual(f.read(), b"@AGENTS.md\n")
        agents = read(self.p("AGENTS.md"))
        for ref in ("@GOALS.md", "@memory-bank/architecture.md", "memory-bank/log.md", "800", "1000"):
            self.assertIn(ref, agents)

    def test_never_overwrites_and_names_the_missing_import(self):
        with open(self.p("GOALS.md"), "w", encoding="utf-8") as f:
            f.write("mine\n")
        with open(self.p("CLAUDE.md"), "w", encoding="utf-8") as f:
            f.write("# my rules\n")
        code, out, _ = self.run_main("init", self.dir)
        self.assertEqual(code, 0)
        self.assertEqual(read(self.p("GOALS.md")), "mine\n")
        self.assertEqual(read(self.p("CLAUDE.md")), "# my rules\n")
        self.assertIn("@AGENTS.md", out)

    def test_second_run_creates_nothing(self):
        self.run_main("init", self.dir)
        code, out, _ = self.run_main("init", self.dir)
        self.assertEqual(code, 0)
        self.assertNotIn("created", out)

    def test_missing_folder_is_an_error(self):
        code, _, err = self.run_main("init", self.p("nope"))
        self.assertEqual(code, 2)
        self.assertIn("not a folder", err)

    def test_templates_are_lf_and_short(self):
        for rel in vg.PROJECT_FILES:
            with open(os.path.join(vg.TEMPLATES, *rel.split("/")), "rb") as f:
                data = f.read()
            self.assertNotIn(b"\r", data, rel)
            self.assertLess(data.count(b"\n"), 60, rel)


class Hook(Base):
    def hook(self, payload):
        raw = payload if isinstance(payload, bytes) else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        return self.run_main("hook", stdin=raw)

    def test_long_file_is_reported_to_claude(self):
        write_lines(self.p("game.py"), 850)
        code, _, err = self.hook({"tool_name": "Write", "tool_input": {"file_path": self.p("game.py")}})
        self.assertEqual(code, 2)
        self.assertIn("850 lines", err)

    def test_hard_limit_is_named(self):
        write_lines(self.p("game.py"), 1200)
        code, _, err = self.hook({"tool_input": {"file_path": self.p("game.py")}})
        self.assertEqual(code, 2)
        self.assertIn("1000", err)

    def test_non_ascii_path(self):
        write_lines(self.p("ömer", "oyun.py"), 900)
        code, _, _ = self.hook({"tool_input": {"file_path": self.p("ömer", "oyun.py")}})
        self.assertEqual(code, 2)

    def test_quiet_for_short_unchecked_missing_or_pathless(self):
        write_lines(self.p("small.py"), 10)
        write_lines(self.p("notes.md"), 900)
        payloads = [{"tool_input": {"file_path": self.p(n)}} for n in ("small.py", "notes.md", "gone.py")]
        payloads += [{"tool_name": "Bash", "tool_input": {"command": "ls"}}, {"tool_input": None}, []]
        for payload in payloads:
            self.assertEqual(self.hook(payload), (0, "", ""), payload)

    def test_bad_input_is_reported_not_hidden(self):
        code, _, err = self.hook(b"not json")
        self.assertEqual(code, 1)
        self.assertIn("unreadable", err)


class Cli(Base):
    def test_unknown_command_prints_usage(self):
        code, _, err = self.run_main("frobnicate")
        self.assertEqual(code, 2)
        self.assertIn("init", err)


class SkillFile(unittest.TestCase):
    def test_frontmatter(self):
        text = read(os.path.join(ROOT, "SKILL.md"))
        m = re.match(r"---\nname: (.+)\ndescription: (.+)\n---\n", text)
        self.assertIsNotNone(m)
        self.assertRegex(m.group(1), r"^[a-z0-9-]{1,64}$")
        self.assertLessEqual(len(m.group(2)), 1024)
        self.assertNotIn('"', m.group(2))
        self.assertNotIn(": ", m.group(2))


if __name__ == "__main__":
    unittest.main()
