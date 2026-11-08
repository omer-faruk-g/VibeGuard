#!/usr/bin/env python3
"""VibeGuard helper. Usage:

  vibeguard.py init [DIR]        create AGENTS.md, CLAUDE.md, GOALS.md and memory-bank/ if missing
  vibeguard.py check [PATH ...]  list files past the size limits (default: current folder)
  vibeguard.py hook              PostToolUse hook: check the file the tool just wrote

Exit codes. init: 0 done, 2 not a folder. check: 0 fine, 1 a file needs a split, 2 bad path.
hook: 0 fine, 2 file too long (stderr goes to Claude), 1 unreadable hook input.
"""
import json
import os
import shutil
import sys

SPLIT_AT = 800   # split a file as soon as it passes this
HARD_MAX = 1000  # no file may pass this

CODE_EXT = {
    ".py", ".pyw", ".rs", ".go", ".c", ".h", ".cc", ".cpp", ".cxx", ".hpp", ".hh",
    ".cs", ".java", ".kt", ".kts", ".scala", ".swift", ".m", ".mm", ".dart",
    ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".vue", ".svelte",
    ".html", ".css", ".scss", ".rb", ".php", ".lua", ".sh", ".bash", ".ps1", ".psm1",
    ".sql", ".zig", ".ex", ".exs", ".erl", ".hs", ".ml", ".clj", ".r", ".jl", ".gd",
    ".glsl", ".wgsl", ".hlsl", ".shader",
}
GENERATED = (".min.js", ".pb.go", "_pb2.py", ".g.dart", ".designer.cs")
SKIP_DIRS = {"node_modules", "target", "dist", "build", "out", "venv", "env",
             "__pycache__", "vendor", "coverage", "obj"}
TEMPLATES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
PROJECT_FILES = ("AGENTS.md", "GOALS.md", "memory-bank/architecture.md", "memory-bank/log.md")
IMPORT_LINE = "@AGENTS.md"


def count_lines(path):
    with open(path, "rb") as f:
        data = f.read()
    return data.count(b"\n") + (1 if data and not data.endswith(b"\n") else 0)


def is_checked(path):
    """Code files, plus the .md notes inside memory-bank/ (they load into AI sessions)."""
    parts = path.replace("\\", "/").lower().split("/")
    name = parts[-1]
    if name.endswith(GENERATED):
        return False
    ext = os.path.splitext(name)[1]
    return ext in CODE_EXT or (ext == ".md" and "memory-bank" in parts[:-1])


def collect(paths):
    for top in paths:
        if os.path.isfile(top):
            yield top  # a file named on the command line is always checked
            continue
        for root, dirs, files in os.walk(top):
            dirs[:] = sorted(d for d in dirs if not d.startswith(".") and d not in SKIP_DIRS)
            for name in sorted(files):
                path = os.path.join(root, name)
                if is_checked(path):
                    yield path


def cmd_check(paths, out, err):
    paths = paths or ["."]
    missing = [p for p in paths if not os.path.exists(p)]
    if missing:
        err.write("vibeguard check: not found: %s\n" % ", ".join(missing))
        return 2
    long_files = []
    for path in collect(paths):
        n = count_lines(path)
        if n > SPLIT_AT:
            long_files.append((n, os.path.normpath(path).replace("\\", "/")))
    if not long_files:
        out.write("VibeGuard check: OK, no file over %d lines\n" % SPLIT_AT)
        return 0
    out.write("VibeGuard check: %d file(s) over %d lines (split at %d, never past %d)\n"
              % (len(long_files), SPLIT_AT, SPLIT_AT, HARD_MAX))
    for n, path in sorted(long_files, reverse=True):
        out.write("  %-5s %6d  %s\n" % ("OVER" if n > HARD_MAX else "SPLIT", n, path))
    return 1


def cmd_init(target, out, err):
    if not os.path.isdir(target):
        err.write("vibeguard init: not a folder: %s\n" % target)
        return 2
    lines = ["VibeGuard init in %s" % os.path.abspath(target)]
    for rel in PROJECT_FILES:
        dest = os.path.join(target, *rel.split("/"))
        if os.path.exists(dest):
            lines.append("  kept     %s (already there: add only what is missing)" % rel)
            continue
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copyfile(os.path.join(TEMPLATES, *rel.split("/")), dest)
        lines.append("  created  %s" % rel)
    claude_md = os.path.join(target, "CLAUDE.md")
    if not os.path.exists(claude_md):
        with open(claude_md, "w", encoding="utf-8", newline="\n") as f:
            f.write(IMPORT_LINE + "\n")
        lines.append("  created  CLAUDE.md (imports AGENTS.md)")
    else:
        with open(claude_md, encoding="utf-8", errors="replace") as f:
            imported = any(line.strip() == IMPORT_LINE for line in f)
        lines.append("  kept     CLAUDE.md" if imported else
                     "  add      the line %s to CLAUDE.md (it exists, so it was not changed)" % IMPORT_LINE)
    lines.append("Next: fill GOALS.md and the Project rules in AGENTS.md with the user.")
    out.write("\n".join(lines) + "\n")
    return 0


def cmd_hook(raw, err):
    try:
        data = json.loads(raw.decode("utf-8-sig") if isinstance(raw, bytes) else raw)
    except ValueError as exc:
        err.write("vibeguard hook: unreadable hook input (%s)\n" % exc)
        return 1
    tool_input = data.get("tool_input") if isinstance(data, dict) else None
    path = tool_input.get("file_path") if isinstance(tool_input, dict) else None
    if not isinstance(path, str) or not os.path.isfile(path) or not is_checked(path):
        return 0
    n = count_lines(path)
    if n <= SPLIT_AT:
        return 0
    limit = "past the hard limit of %d" % HARD_MAX if n > HARD_MAX else "past %d, split it now" % SPLIT_AT
    err.write("VibeGuard: %s is now %d lines (%s). One job per file: move each responsibility "
              "to its own file, then update memory-bank/architecture.md. If it was this long "
              "before your change, finish the current task first, then propose the split.\n"
              % (path, n, limit))
    return 2


def main(argv=None, stdin=None, out=None, err=None):
    argv = sys.argv[1:] if argv is None else argv
    out = sys.stdout if out is None else out
    err = sys.stderr if err is None else err
    cmd, args = (argv[0], argv[1:]) if argv else ("", [])
    if cmd == "init" and len(args) <= 1:
        return cmd_init(args[0] if args else ".", out, err)
    if cmd == "check":
        return cmd_check(args, out, err)
    if cmd == "hook" and not args:
        return cmd_hook(sys.stdin.buffer.read() if stdin is None else stdin, err)
    err.write(__doc__)
    return 2


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    sys.exit(main())
