# Tools

Command-line tools for this fork. They run Path of Building's own LuaJIT (`runtime/lua51.dll`)
through Python, so no LuaJIT, busted or Docker installation is needed (Windows, 64-bit Python).

## Modifier coverage report

Lists every modifier line Path of Building cannot parse (and therefore cannot calculate), maps it
to the official game stat id, and estimates whether it matters (Offence / Defence) or not
(Utility / Cosmetic).

```
python tools/runlua.py tools/ModCoverageReport.lua
```

Writes `reports/coverage.md` (readable) and `reports/coverage.json` (for tools and AI). If a
previous `reports/coverage.json` exists, the new report lists what became unsupported or supported
since then, so run it after every data update. It also compares the latest passive tree with the
previous one (`--tree-compare 3_29` to choose another version).

For a single build (equipped items and allocated passives only):

```
python tools/runlua.py tools/ModCoverageReport.lua --build "path/to/build.xml"
```

`reports/coverage.*` is committed as the baseline; per-build reports are git-ignored.

## Build library

Collects builds you choose, summarises them with Path of Building and indexes them in SQLite, so
you (and later an AI) can search them and see what similar builds have in common.

Builds come in by hand, never by scraping. poe.ninja's builds / profiles API is closed to
third-party use (see their API docs), so use its PoB button to open a build in Path of Building
and save it, or import a character from your account (the official API that PoB already uses).

```
python tools/library.py add src/Builds --source "poe.ninja streamers" --note "why this build" --tag mybuild
python tools/library.py add --code "<PoB share code>" --name "Forum build"
python tools/library.py list
python tools/library.py show MeiMax
python tools/library.py search --item Soulwrest --ascendancy Luminary
python tools/library.py common --skill "Summon Phantasm"
python tools/library.py rebuild
```

Everything lives in `library/` (git-ignored, it contains account and character names):
`raw/` keeps each original build unchanged, `summary/` the JSON written by
`tools/BuildSummary.lua`, and `builds.db` the index. After a Path of Building or game data
update, `rebuild` recalculates every build from its raw file.

A single build can also be summarised without the library:

```
python tools/runlua.py tools/BuildSummary.lua "path/to/build.xml" "C:/absolute/path/out.json"
```

Tests: `python -m unittest discover tools/tests`

## AI tools (MCP server)

`tools/pob_mcp.py` lets an AI assistant such as Claude use Path of Building and the build library
through the Model Context Protocol. It needs no extra packages. Path of Building stays loaded in a
background worker (`tools/PobWorker.lua`), so after the first call (~4 s) a simulation takes about
a second.

Claude Code picks it up from `.mcp.json` at the repository root (approve it when asked):

```json
{"mcpServers": {"path-of-building": {"command": "python", "args": ["tools/pob_mcp.py"]}}}
```

| Tool | What it does |
|---|---|
| `pob_list_builds` | List or filter library builds |
| `pob_build_summary` | Full structured summary of a build |
| `pob_metrics` | Key numbers (DPS, minion DPS, life, ES, EHP, max hits, resistances) |
| `pob_simulate` | Apply gem / item / passive / config changes to a copy and compare before and after |
| `pob_find_uniques` | Uniques by tags and slot |
| `pob_find_passives` | Passive nodes by tags |
| `pob_list_tags` | All tags |
| `library_common` | What matching builds have in common |
| `library_item_usage` | How often an item appears, by ascendancy, skill and slot |

| `pob_contributions` | Remove each item, support and notable on its own; report DPS / EHP lost and a role |
| `pob_save_build_settings` | Save play-verified settings for a build |

### Play-verified settings and contribution analysis

PoB's defaults are not always how a build is played: it picks a minion's first skill (a Phantasm's
melee attack instead of its spell projectile), and conditions such as withered stacks default to 0.
Settings confirmed in play are saved per library build and applied by every tool and analysis:

```
python tools/library.py settings MeiMax --group 11 --minion-skill "Physical Projectile" --config multiplierWitheredStackCount=15 --note "why"
python tools/library.py analyze MeiMax
```

### Analysing builds: the inbox workflow

1. Open a build in PoB (poe.ninja PoB button, share code or account import) and write in its
   **Notes** tab, e.g. `來源: poe.ninja`, `目的: 看防禦`, `召喚物技能: Physical Projectile`,
   `已知: 打王很強` (English keys `source`, `purpose`, `minion skill`, `main skill`, `known` work too).
2. **Save As** into `src/Builds/inbox/` (any number of builds).
3. Run `python tools/library.py inbox`.

Each build is added to the library, the Notes become verified settings, and a full analysis
(about 2 to 4 minutes per build) writes `library/reports/<build>.md`: PoB numbers with and
without inferred conditions, the damage formula from PoB's breakdown, contributions of items,
supports, notables and every modifier line, the author's Config assumptions, unsupported
modifiers and **questions for the player**. A batch report compares the run and lists core parts
those builds rely on that builds tagged `my-build` do not use. Processed files move to
`src/Builds/done/`. `python tools/library.py report <build>` runs the same analysis for one
library build. Answers to the questions become verified settings or knowledge base facts.

### Mechanics knowledge base

`src/Data/Mechanics.lua` describes game mechanics as data: rules with their numbers, the tags a
mechanic implies (Withered -> chaos, Unholy Might -> withered and chaos), how items and passives
are recognised, and facts. Every rule and fact names its source: `wiki` (PoE Wiki, CC BY-NC),
`pobdata` (PoB's game data export) or `play` (confirmed in play). The tagger, the condition
inference and the AI tools all read it, so a correction made there reaches all of them.

- `pob_mechanics` returns an entry with the uniques and passives that provide it.
- `library_core_parts` (CLI: `library.py core --tag minion`) aggregates saved analyses: which
  parts carry damage, defence or mechanics in that kind of build. It gets better with every
  analysed build.

### Condition inference

Some Config values default to 0 although the build produces them. `tools/lib/inference.lua`
estimates them and the tools apply the estimate unless the build or a request sets the value.
First case, withered stacks (rules from the PoE Wiki): `min(15, hits per second x chance x 2 s)`,
summed over the player and every minion alive, with Unholy Might counted as a 25% chance. The
result lists its sources and assumptions (by default all minions alive, i.e. steady state); pass
`infer: false` to compare, or `minionCount` for the start of a fight.

`analyze` removes each part on its own and records the DPS and EHP lost. Roles: *enables main
skill*, *core damage* / *damage*, *core defence* / *defence*, *functional* (PoB measures nothing,
but the part drives mechanics it does not model, e.g. minion count or triggers), *tree hub*
(removing the notable disconnects many points). Results are stored and shown by `show`.

Builds are named by library id prefix or name, or by a path to a `.xml` file. Every summary lists
the modifiers PoB does not calculate and the Config assumptions, so advice can say how far the
numbers can be trusted.

## Play log (Client.txt)

The game writes `logs/Client.txt` in its install folder: areas generated (id, level, seed), areas entered, deaths and
level-ups. `tools/clientlog.py` turns it into map runs (time per map, portals, deaths) for comparing play with PoB.

1. On the game PC, export the useful lines (chat and whispers are removed) to `ClientLog-<date>.txt` on the Desktop:

       irm https://raw.githubusercontent.com/xingqiang1120/PathOfBuilding/feature/ai-tools/tools/export_clientlog.ps1 | iex

   or `powershell -ExecutionPolicy Bypass -File tools/export_clientlog.ps1 -Days 60 -Path "<game>\logs\Client.txt"`.
2. Copy the file here and import it: `python tools/clientlog.py import <file>` (a raw Client.txt works too).
3. `python tools/clientlog.py summary [--character NAME] [--level 83]`, or the `play_log` MCP tool.
   `python tools/clientlog.py templates` lists system messages not recognised yet (e.g. from a localized client).

The parsed log is stored in `library/playlogs/` (git-ignored). Client.txt has no hit sizes or causes of death.

## Running Lua scripts and tests

```
python tools/runlua.py <script.lua> [args...]
```

The script starts in `src/` and can `dofile("HeadlessWrapper.lua")`; its arguments are in the
global `SCRIPT_ARGS`. The official test suite still needs busted (see CONTRIBUTING.md).
