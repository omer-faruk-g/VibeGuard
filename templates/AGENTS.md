# AI rules for this project

Every AI session reads this file first and follows it 100%. Read these two with it (Claude Code loads them automatically):

@GOALS.md
@memory-bank/architecture.md

Before the first change, read the newest entries at the top of memory-bank/log.md.

## Always
- Put new code where memory-bank/architecture.md says it belongs. A new job gets its own file or module, never the main file.
- One job per file. Split a file as soon as it passes 800 lines; no file may pass 1000.
- Keep the core independent: features depend on the core, the core never imports a feature, and a failure in a feature must not break the core.
- Build in small steps from the building blocks in GOALS.md. Every step ends runnable.
- After every step, run it (not only build it) and report the real result.
- After every change or fix, add an entry at the top of memory-bank/log.md. Update memory-bank/architecture.md when the structure changes.
- Pick the design that still holds after the next building blocks, not the quickest patch. If a shortcut adds debt, say so and log it.

## Never
- Never add unrelated code to a file just because it is already open.
- Never call something done or working because it compiles.
- Never widen or change the GOALS.md scope without asking.
- Never restart from scratch or stack workarounds to dodge a design problem: log it and fix it.

## Project rules
<!-- Do and don't rules for this stack, for example: no unsafe in Rust unless the log entry says why; no global mutable state; all file and network IO lives in one io module. -->
