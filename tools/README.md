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

## Running Lua scripts and tests

```
python tools/runlua.py <script.lua> [args...]
```

The script starts in `src/` and can `dofile("HeadlessWrapper.lua")`; its arguments are in the
global `SCRIPT_ARGS`. The official test suite still needs busted (see CONTRIBUTING.md).
