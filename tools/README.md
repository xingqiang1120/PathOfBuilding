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

## Running Lua scripts and tests

```
python tools/runlua.py <script.lua> [args...]
```

The script starts in `src/` and can `dofile("HeadlessWrapper.lua")`; its arguments are in the
global `SCRIPT_ARGS`. The official test suite still needs busted (see CONTRIBUTING.md).
