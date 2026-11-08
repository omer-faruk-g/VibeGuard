# VibeGuard

A Claude Code skill that keeps vibe-coded projects from collapsing under architecture debt.

AI coding tools write the average, shortest-term design. That works for a demo. In a real project it piles up: one giant main file, no module boundaries, features nobody ran, until the project stalls halfway. VibeGuard turns vibe coding into a process that catches the AI's mistakes while they are cheap.

## What it does

**Three project files the AI reads every session**

| File | Job |
|---|---|
| `AGENTS.md` | Do and don't rules. `CLAUDE.md` imports it, so Claude Code loads it every session; Codex, Cursor and many other agents read it directly. It imports the next two files. |
| `GOALS.md` | Goal, in scope, out of scope, building blocks, done when. |
| `memory-bank/` | `architecture.md` (the module map) and `log.md` (one entry per change or fix, so the next session, or a different model, continues where the last one stopped). |

**Five rules against the usual failure modes**

1. Modular code with an independent core: an error outside the core never reaches it.
2. One job per file: split at 800 lines, never past 1000.
3. Small runnable building blocks instead of giant requests.
4. Run and test every feature right away: compiling is not working.
5. Fix new design problems one by one instead of restarting.

**`scripts/vibeguard.py`** (Python 3.8+, no dependencies)

- `init` creates the files above, only those that are missing; it never overwrites.
- `check [PATH ...]` lists files over 800 lines and exits 1 when one needs a split.
- `hook` checks each file Claude writes (optional PostToolUse hook).

## Install

```bash
git clone https://github.com/omer-faruk-g/VibeGuard "$HOME/.claude/skills/vibeguard"
```

Claude uses the skill when you start a project, ask for a big feature, when a file grows, and when you say `vibeguard`.

## Use

In the project root:

```bash
python "$HOME/.claude/skills/vibeguard/scripts/vibeguard.py" init
```

```bash
python "$HOME/.claude/skills/vibeguard/scripts/vibeguard.py" check
```

## Optional hook

Add this to `~/.claude/settings.json` to check every file right after Claude writes it:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          { "type": "command", "command": "python \"$HOME/.claude/skills/vibeguard/scripts/vibeguard.py\" hook" }
        ]
      }
    ]
  }
}
```

On Windows, if `python` or `$HOME` does not resolve inside hooks, use full paths, for example `"C:/path/to/python.exe" "C:/Users/you/.claude/skills/vibeguard/scripts/vibeguard.py" hook`.

## Tests

```bash
cd "$HOME/.claude/skills/vibeguard" && python -m unittest discover -s tests -q
```

## Credit

The rules follow the ideas in the Turkish video [Vibe Coding'in Acı Gerçeği: Projelerin %90'ı Neden Yarım Kalıyor?](https://youtu.be/vU_NwrDDrQA). The file names, the script, the hook and the split of the memory bank into a map and a log are additions.

## Türkçe

VibeGuard, yapay zekâyla yazılan projelerin mimari borç altında yarım kalmasını önleyen bir Claude Code skill'i. Proje başında üç dosya kurar: kurallar için `AGENTS.md`, hedef ve kapsam için `GOALS.md`, mimari harita ve değişiklik günlüğü için `memory-bank/`. Kodlarken beş kural uygular: bağımsız çekirdekle modüler kod, dosya başına tek iş ve 800 satırda bölme, küçük ve çalışan adımlar, her özelliği hemen çalıştırıp test etme, yeni sorunları baştan başlamadan tek tek çözme. `vibeguard.py check` dosya boyutlarını ölçer.

## License

GPL-3.0. See [LICENSE](LICENSE).
