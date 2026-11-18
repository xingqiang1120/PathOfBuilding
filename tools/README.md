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

## Running Lua scripts and tests

```
python tools/runlua.py <script.lua> [args...]
```

The script starts in `src/` and can `dofile("HeadlessWrapper.lua")`; its arguments are in the
global `SCRIPT_ARGS`. The official test suite still needs busted (see CONTRIBUTING.md).
