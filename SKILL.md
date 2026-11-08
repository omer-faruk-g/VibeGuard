---
name: vibeguard
description: VibeGuard - keeps vibe-coded projects modular. Scaffolds AGENTS.md, GOALS.md and memory-bank/ at project start, splits files at 800 lines and never past 1000 (vibeguard.py check), builds in small runnable blocks and tests each feature right away. Use when starting or setting up a project, when a file or the main file grows large, when the user asks for a whole app or engine at once, after each change or fix, and when the user says vibeguard, vibe coding, proje kur, proje iskeleti, memory bank, dosya çok büyüdü, modüler yap.
---

# VibeGuard

AI coding tools write the average, shortest-term design. That is fine for a demo and fatal for a real project: one giant main file, no module boundaries, features nobody ran, until the project stalls halfway under architecture debt. VibeGuard does not make the AI perfect; it sets up a process that catches its mistakes while they are cheap.

No AGENTS.md or memory-bank/ in the project yet: start at step 1. Otherwise start at step 2.

## 1. Project start (once)

From the project root:

    python "$HOME/.claude/skills/vibeguard/scripts/vibeguard.py" init

Use `python3` where `python` is missing. The script creates only missing files and never overwrites:

| File | Job |
|---|---|
| AGENTS.md | Do and don't rules every AI session follows 100%. It imports GOALS.md and memory-bank/architecture.md, so they load with it. Codex, Cursor and many other agents read AGENTS.md directly. |
| CLAUDE.md | One line, `@AGENTS.md`, so Claude Code loads the rules in every session. |
| GOALS.md | Goal, in scope, out of scope, building blocks in order, done when. Stops scope drift. |
| memory-bank/architecture.md | Module map (module, its one job, what it may depend on), boundaries, decisions. |
| memory-bank/log.md | One entry per change or fix, newest first, so the next session or another model can continue. |

Then:
- Fill GOALS.md and the Project rules section of AGENTS.md together with the user. Ask for the goal and the scope; never invent them.
- A file the script kept because it already existed: read it and add only the missing parts. If CLAUDE.md existed, add the `@AGENTS.md` line the script printed.
- AGENTS.md, GOALS.md and architecture.md load in every session, so keep each one short (under about 60 lines).

## 2. Every session

- Before the first change, have AGENTS.md with its imports in context and read the newest entries at the top of memory-bank/log.md. Without the CLAUDE.md import, read the files yourself.
- Follow AGENTS.md 100%. When a request conflicts with it or with the GOALS.md scope, say so and ask before doing it.

## 3. The five failure modes

1. **Not modular.** Keep a core that knows nothing about features. Features depend on the core, never the other way round, and a failure outside the core must not reach it. Use the language's own unit of isolation: crates in a Rust workspace, Python packages, JS/TS packages or folders with one entry file, Go packages, C# projects. Add each new module to architecture.md before writing it.
2. **One giant file (God Object).** One job per file, the Unix way. Split a file as soon as it passes 800 lines; no file may pass 1000. Split by responsibility, not at an arbitrary line, and update architecture.md. The entry file only wires modules together. Big files also make the AI slower and more forgetful. A file that was already too long before the task: finish the task first, then propose the split as the next step.
3. **Giant requests.** "Make me a game engine" is not one step. Break it into building blocks that each run on their own, smallest first: a wgpu engine starts as an empty window, then a clear color, then one triangle. Write the list into GOALS.md, confirm the order with the user, and build one block at a time. Design each block so the next ones fit, but do not build future blocks early.
4. **Untested features.** After each block or fix, run it, not just build it: compiling is not working. Run the tests or the program, read the real output, report it, and ask the user to try what only a person can judge (UI, feel, hardware). Move on only when it works.
5. **Expecting perfection.** Every new feature exposes new design problems; that is normal. Log each one in the Open line, fix them one at a time, and never restart from scratch or stack workarounds. When the same problem keeps coming back, fix the structure in architecture.md instead of the symptom.

Under all five: before each change, look up where it belongs in architecture.md and pick the design that still holds after the next building blocks, not the quickest patch. If you take a shortcut anyway, say so and log it as debt.

## 4. After every change or fix

Add an entry at the top of memory-bank/log.md, right below the marker line:

    ## YYYY-MM-DD - short title
    - What: the change
    - Why: the reason or the bug
    - Files: the files touched
    - Tested: the command you ran and its real result
    - Open: problems found, next step

Write it for a model that has never seen the project: facts and file names, no chat history. Update architecture.md when modules or boundaries changed. When log.md passes 800 lines, move the oldest entries to memory-bank/archive/.

## 5. Size check

    python "$HOME/.claude/skills/vibeguard/scripts/vibeguard.py" check [PATH ...]

Lists code files, and the notes in memory-bank/, over 800 lines, longest first: SPLIT past 800, OVER past 1000. Hidden folders, node_modules, target, dist, build, vendor and similar folders and generated files such as .min.js are skipped; a file named on the command line is always checked. Exit 0 means fine, 1 means a file needs a split, 2 means a bad path. Run it after a big change and before calling a block done.

The script also has a `hook` mode for a PostToolUse hook on Write|Edit|MultiEdit: it checks each file right after Claude writes it and tells Claude when the file passes 800 lines. Adding it changes settings.json, so add it only with the user's OK; README.md has the snippet.

## Other skills

Stricter rules from other installed skills win, for example plan approval before multi-file changes or evidence before saying done. VibeGuard adds only the project files, the module map, the size limits and the small-blocks order.
