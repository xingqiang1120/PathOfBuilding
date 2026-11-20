"""MCP server that lets an AI assistant use Path of Building and the build library.

Speaks the Model Context Protocol over stdio (newline-delimited JSON-RPC 2.0) with no third-party
dependencies. Path of Building runs in a persistent background worker (tools/PobWorker.lua), so
only the first call pays the ~4 s load time; a simulation then takes about a second.

Register it with Claude Code, for example in .mcp.json at the repository root:

    {"mcpServers": {"pob": {"command": "python", "args": ["tools/pob_mcp.py"]}}}

Tools: see TOOLS below. Builds are referred to by a library id prefix or name (tools/library.py)
or by a path to a PoB build .xml file.
"""
import json
import os
import sys
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import library  # noqa: E402
import clientlog  # noqa: E402
import simlog  # noqa: E402
from pob_worker import WORKER, WorkerError  # noqa: E402

SERVER_INFO = {"name": "path-of-building", "version": "0.1.0"}
DEFAULT_PROTOCOL = "2025-06-18"

INSTRUCTIONS = """Path of Building (PoB) for Path of Exile 1, run headless, plus a local library of saved builds.
- Numbers come from PoB's own calculation. Every build summary lists modifier lines PoB does NOT calculate
  ("coverage.unsupported") and the Config assumptions it relies on ("config"); mention them when they affect advice.
- For minion builds the DPS is per minion; the number of minions alive is not modelled. PoB picks a minion's first skill
  by default, which may not be the one it really uses: check "minionSkills" and ask the user.
- Conditions PoB leaves at 0 (currently withered stacks) are inferred from the build and applied automatically; results
  carry "inferred" with the estimate and assumptions (e.g. all minions alive). Mention them; pass infer=false to compare.
- Builds can carry play-verified settings (group, minion skill, Config); tools apply them automatically. Save new ones with
  pob_save_build_settings only after the user confirms them.
- Results carry "buildChecks" when the build was corrected on load or looks inconsistent: the guardian's item set worn by
  the player, or Animate Guardian (Weapon) left on the player's gear (both fixed automatically; checkBuild=false skips it), and
  more mana/life reserved than available. Old Luminary builds put the mercenary's auras on the player because PoB had no
  mercenary: ask which auras are the mercenary's and model them with the mercenary setting instead. Character import from
  the official API has no guardian gear; it must be entered by hand in an item set named "Animate Guardian".
- A build's Config holds its author's assumptions (e.g. 50 corpses consumed recently, tested while mapping). Use
  pob_scenarios to show which assumptions hold for mapping and which for a single boss, and say which content a build is for.
- Use pob_simulate to check a suggestion before recommending it, and report the before/after numbers.
- Tags (pob_list_tags) classify items and passives, e.g. minion, phantasm, energyshield, fire. Mechanic tags (unholymight,
  withered, ...) imply related tags (withered -> chaos). Check pob_mechanics for how a mechanic works and where its numbers
  come from before relying on memory; say when a fact is only "play"-confirmed or not covered."""

CHANGE_SCHEMA = {
    "type": "object",
    "description": "One change. Types: minion_skill {skill}; gem_replace {gem, with, group?, level?, quality?}; gem_add {group, gem, level?}; "
                   "gem_remove {gem, group?}; gem_level {gem, level?, quality?}; main_group {group}; "
                   "item_equip {slot, unique | raw}; item_remove {slot}; passive_add {node}; passive_remove {node}; "
                   "config_set {key, value}. group = socket group number or the name of a gem in it. "
                   "slot = PoB slot name, e.g. Helmet, Body Armour, Weapon 1, Ring 2, Flask 3.",
    "properties": {
        "type": {"type": "string", "enum": ["minion_skill", "gem_replace", "gem_add", "gem_remove", "gem_level", "main_group", "item_equip",
                                            "item_remove", "passive_add", "passive_remove", "config_set"]},
        "gem": {"type": "string"}, "with": {"type": "string"}, "group": {"type": ["integer", "string"]},
        "level": {"type": "integer"}, "quality": {"type": "integer"}, "slot": {"type": "string"},
        "unique": {"type": "string"}, "raw": {"type": "string", "description": "Item text as copied from the game or PoB"},
        "node": {"type": ["string", "integer"], "description": "Passive name or node id"},
        "key": {"type": "string"}, "value": {}, "skill": {"type": ["string", "integer"], "description": "Minion skill name or index"},
    },
    "required": ["type"],
}
MAIN_PROPS = {
    "group": {"type": ["integer", "string"], "description": "Socket group to treat as main skill (default: saved setting, else strongest)"},
    "minionSkill": {"type": ["string", "integer"], "description": "Skill the minion really uses, e.g. 'Physical Projectile' (default: saved setting, else PoB's first skill)"},
    "ignoreSettings": {"type": "boolean", "description": "Ignore the build's saved play-verified settings"},
    "checkBuild": {"type": "boolean", "description": "Correct item-set mistakes on load (guardian gear worn by the player, Animate Guardian's Weapon on the player's set); default true"},
    "infer": {"type": "boolean", "description": "Estimate Config values the build leaves at 0, e.g. withered stacks from wither chance x hits per second (default true)"},
    "minionCount": {"type": "integer", "description": "Minions alive for inference (default: the minion limit, i.e. steady state)"},
    "mercenary": {"type": "object", "description": "Luminary mercenary, modelled as a Party member. By class (see pob_mercenaries): {class, skills: [rolled "
                                                   "secondary and utility skills], supports: {skill: [e.g. 'Curse Effect III']}, levels: {skill: level}, life}; "
                                                   "primary skills are always included. Or explicit: {auras: [{name, level}], curses: [{name, level}], life}. "
                                                   "Auras (with Bestowed Knighthood's increased effect) reach you and your minions; curses share the curse "
                                                   "slots; life enables Loyal Bodyguard. Skill numbers are gem-based estimates. Default: saved setting"},
    "summonRate": {"type": "number", "description": "Minions summoned per second in play (e.g. phantasms from corpses). Needed for Fresh Meat uptime; "
                                                     "minion DPS is then blended between buffed and unbuffed minions (default: saved setting)"},
}
BUILD_ARG = {"type": "string", "description": "Library build id prefix or name, or a path to a PoB build .xml file"}
FILTER_PROPS = {k: {"type": "string"} for k in library.FILTERS}

TOOLS = [
    {"name": "pob_list_builds",
     "description": "List or filter builds in the local library (ascendancy, skill, item, passive, tag, text; partial matches).",
     "inputSchema": {"type": "object", "properties": FILTER_PROPS}},
    {"name": "pob_build_summary",
     "description": "Full structured summary of a build: character, skill groups with calculated DPS, primary skill, equipped "
                    "items with tags and mod lines, passives, key stats, Config assumptions and modifiers PoB does not calculate.",
     "inputSchema": {"type": "object", "properties": {"build": BUILD_ARG, "refresh": {"type": "boolean", "description": "Recalculate instead of using the saved library summary"}},
                     "required": ["build"]}},
    {"name": "pob_metrics",
     "description": "Current key numbers of a build (DPS incl. minion DPS and minion skills, life, ES, EHP, max hit taken per damage type, "
                    "resistances, block, attributes). Saved play-verified settings are applied unless ignoreSettings.",
     "inputSchema": {"type": "object", "properties": dict(MAIN_PROPS, build=BUILD_ARG), "required": ["build"]}},
    {"name": "pob_simulate",
     "description": "Apply changes to a copy of a build (gems, items, passives, config, minion skill) and return the numbers before and after, "
                    "with every stat that changed. Saved play-verified settings form the baseline. The saved build is never modified.",
     "inputSchema": {"type": "object", "properties": dict(MAIN_PROPS, build=BUILD_ARG, changes={"type": "array", "items": CHANGE_SCHEMA}),
                     "required": ["build", "changes"]}},
    {"name": "pob_contributions",
     "description": "Leave-one-out analysis: remove each item, support gem and notable/keystone on its own and report the DPS and EHP lost, "
                    "with a role (core damage, defence, enables main skill, functional = matters for mechanics PoB does not measure). "
                    "Explains how a build works. Takes about a second per part; library results are saved.",
     "inputSchema": {"type": "object", "properties": dict(MAIN_PROPS, build=BUILD_ARG, includePassives={"type": "boolean"},
                                                          changes={"type": "array", "items": CHANGE_SCHEMA}), "required": ["build"]}},
    {"name": "pob_infer_conditions",
     "description": "Explain the Config values PoB leaves at 0 that this build can actually produce, e.g. withered stacks: sources and their "
                    "chance, hits per second, minions, duration, the estimate and its assumptions. Other tools apply these by default.",
     "inputSchema": {"type": "object", "properties": dict(MAIN_PROPS, build=BUILD_ARG), "required": ["build"]}},
    {"name": "pob_damage_breakdown",
     "description": "The main skill's damage formula from PoB's own calculation: per damage type the base damage, increased and more "
                    "multipliers, conversion, enemy mitigation (resistance, damage taken), plus speed, hit chance, crit and DoT. "
                    "Use it to explain where damage comes from and which multiplier a change would affect.",
     "inputSchema": {"type": "object", "properties": dict(MAIN_PROPS, build=BUILD_ARG), "required": ["build"]}},
    {"name": "pob_config_sensitivity",
     "description": "Switch off each Config assumption the build turned on (conditions, charges, buffs, boss setting) and report the DPS "
                    "and EHP change, to show which assumptions the numbers depend on.",
     "inputSchema": {"type": "object", "properties": dict(MAIN_PROPS, build=BUILD_ARG), "required": ["build"]}},
    {"name": "pob_scenarios",
     "description": "The build in three fights: asSaved (its own Config, the author's assumptions), mapping (normal monsters, the author's "
                    "density assumptions kept) and boss (one pinnacle boss alone). Lists every Config assumption the build relies on "
                    "with its kind - density (corpses, kills, nearby enemies: re-estimated for a boss from what the build makes itself), "
                    "fightPhase (enemy on low life: blended by share of the fight), sustained (charges, rage, buffs: checked for a "
                    "source in the build, uptime estimated where the wording allows; noSource = only a Config setting) - the value "
                    "per scenario, the reason and the DPS change of the boss value alone. Use it to explain what a build is made for.",
     "inputSchema": {"type": "object", "properties": dict(MAIN_PROPS, build=BUILD_ARG), "required": ["build"]}},
    {"name": "pob_full_analysis",
     "description": "Full analysis of a library build, as tools/library.py report: numbers with and without inference, damage formula, "
                    "contributions of items/supports/notables and of every modifier line, Config assumptions, unsupported modifiers, and "
                    "questions only the player can answer. Takes a few minutes. Returns the Markdown report and the questions.",
     "inputSchema": {"type": "object", "properties": {"build": BUILD_ARG, "includePassives": {"type": "boolean"}}, "required": ["build"]}},
    {"name": "pob_save_build_settings",
     "description": "Save play-verified settings for a library build so every later analysis uses them: main group, the skill its minions "
                    "really use, and Config changes (e.g. withered stacks). Only save what the user confirmed. Omitted fields keep their value.",
     "inputSchema": {"type": "object", "properties": {"build": BUILD_ARG, "group": MAIN_PROPS["group"], "minionSkill": MAIN_PROPS["minionSkill"],
                                                      "summonRate": MAIN_PROPS["summonRate"], "mercenary": MAIN_PROPS["mercenary"], "changes": {"type": "array", "items": CHANGE_SCHEMA}, "note": {"type": "string"}},
                     "required": ["build"]}},
    {"name": "pob_mercenaries",
     "description": "Mercenary roster (PoE Wiki): each class with its fixed skill pools - primary skills (always), secondary and utility "
                    "skills (pick N of the options) - and what each skill does for the player: aura, curse, mark (calculated), ally (not "
                    "calculated yet) or self. Filter by class name, attribute (e.g. 'Int') or house.",
     "inputSchema": {"type": "object", "properties": {"class": {"type": "string"}}}},
    {"name": "pob_find_uniques",
     "description": "Find unique items by tags (all must match) and optional slot or item type, e.g. tags [minion, energy shield], slot Helmet.",
     "inputSchema": {"type": "object", "properties": {"tags": {"type": "array", "items": {"type": "string"}}, "slot": {"type": "string"},
                                                      "limit": {"type": "integer"}}, "required": ["tags"]}},
    {"name": "pob_find_passives",
     "description": "Find passive tree nodes in the latest tree by tags. types defaults to [Notable, Keystone]; add Ascendancy or Normal as needed.",
     "inputSchema": {"type": "object", "properties": {"tags": {"type": "array", "items": {"type": "string"}},
                                                      "types": {"type": "array", "items": {"type": "string"}},
                                                      "ascendancy": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["tags"]}},
    {"name": "pob_list_tags",
     "description": "All tags (id, label, category, parent) usable in pob_find_uniques and pob_find_passives.",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "library_common",
     "description": "What builds matching the filters have in common: share of builds using each unique, gem, notable, ascendancy node and tag.",
     "inputSchema": {"type": "object", "properties": dict(FILTER_PROPS, top={"type": "integer"})}},
    {"name": "pob_mechanics",
     "description": "Mechanics knowledge base: rules with their numbers (e.g. Withered: 15 stacks, 6% chaos damage taken each, 2 s), "
                    "implied tags, sourced facts (wiki / PoB data / confirmed in play) and the uniques and passives that provide the "
                    "mechanic. Use it to check how a mechanic works before reasoning about it. id or query optional.",
     "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}, "query": {"type": "string"}}}},
    {"name": "library_core_parts",
     "description": "Across analysed library builds matching the filters (e.g. tag minion, ascendancy Necromancer): which items, supports "
                    "and passives are core for damage, defence, or functional (mechanics PoB does not measure), with average loss when removed.",
     "inputSchema": {"type": "object", "properties": dict(FILTER_PROPS, top={"type": "integer"})}},
    {"name": "play_log",
     "description": "The user's real play, from the game's own Client.txt (imported with tools/clientlog.py): map runs with time per "
                    "map, portals used and deaths, by area level and map, the slowest runs and the latest deaths. Use it to compare "
                    "PoB's predictions with play (e.g. deaths per map vs the one-shot threshold). It has no hit sizes or causes of death. "
                    "Filters: character (deaths), since (YYYY-MM-DD), level (area level).",
     "inputSchema": {"type": "object", "properties": {"character": {"type": "string"}, "since": {"type": "string"},
                                                      "level": {"type": "integer"}, "top": {"type": "integer"}}}},
    {"name": "sim_stats",
     "description": "What the build generator and optimizer learned from every candidate they tried in PoB (tools/simlog.py): the "
                    "average DPS and EHP change of each change (passive per point, support, aura, item), filtered by context - "
                    "skill (name or a word such as 'wand', 'minion', 'spell'), ascendancy, kind (passive_add, gem_add, gem_replace, "
                    "group_add, item_set). Averages over different builds: a guide for what to try, not a calculation; confirm "
                    "with pob_simulate. Without filters: a summary of runs and samples.",
     "inputSchema": {"type": "object", "properties": {"kind": {"type": "string"}, "skill": {"type": "string"}, "ascendancy": {"type": "string"},
                                                      "top": {"type": "integer"}}}},
    {"name": "library_item_usage",
     "description": "How often an item appears in the library, grouped by ascendancy, primary skill and slot, with the builds using it.",
     "inputSchema": {"type": "object", "properties": {"item": {"type": "string"}, "top": {"type": "integer"}}, "required": ["item"]}},
]


def log(*args):
    print(*args, file=sys.stderr, flush=True)


class ToolError(Exception):
    """An error the AI can act on (bad build name, unknown gem, ...)."""


def resolve_build(key):
    """Return (xml, name, library_id or None, saved settings) for a library key or an .xml path."""
    try:
        xml, name, build_id = library.resolve(key)
    except LookupError as e:
        raise ToolError(f"{e} (use pob_list_builds)")
    return xml, name, build_id, library.get_settings(build_id)


def worker_params(args, xml, name, settings):
    overrides = {"group": args.get("group"), "minionSkill": args.get("minionSkill"), "changes": args.get("changes") or [],
                 "infer": args.get("infer"), "minionCount": args.get("minionCount"), "summonRate": args.get("summonRate"),
                 "mercenary": args.get("mercenary"), "checkBuild": args.get("checkBuild")}
    if args.get("ignoreSettings"):
        settings = {}
    return library.apply_settings({"xml": xml, "name": name}, settings, overrides)


def tool_build_summary(args):
    xml, name, build_id, settings = resolve_build(args["build"])
    summary = None
    if build_id and not args.get("refresh"):
        path = os.path.join(library.LIBRARY, "summary", build_id + ".json")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                summary = json.load(f)
    if summary is None:
        summary = WORKER.call("summary", {"xml": xml, "name": name})
    summary.pop("tagInfo", None)
    if settings:
        summary["verifiedSettings"] = settings
    return summary


def tool_metrics(args):
    xml, name, _, settings = resolve_build(args["build"])
    params = worker_params(args, xml, name, settings)
    if params.get("changes"):
        # Saved config changes are applied through a simulation; report its result state
        result = WORKER.call("simulate", params)["after"]
    else:
        result = WORKER.call("metrics", params)
    result["settingsApplied"] = {k: params[k] for k in ("group", "minionSkill", "changes") if params.get(k)}
    return result


def tool_simulate(args):
    xml, name, build_id, settings = resolve_build(args["build"])
    if args.get("ignoreSettings"):
        settings = {}
    base = library.apply_settings({"xml": xml, "name": name}, settings, {"group": args.get("group"), "minionSkill": args.get("minionSkill"),
                                                                          "infer": args.get("infer"), "minionCount": args.get("minionCount"),
                                                                          "summonRate": args.get("summonRate"), "mercenary": args.get("mercenary"), "checkBuild": args.get("checkBuild")})
    # Saved settings form the baseline; the requested changes are what is compared
    saved_changes = base.pop("changes")
    params = dict(base, changes=saved_changes + list(args.get("changes") or []))
    if saved_changes:
        before = WORKER.call("simulate", dict(base, changes=saved_changes))["after"]
        result = WORKER.call("simulate", params)
        result["before"] = before
        result["inferredBefore"] = WORKER.call("infer", dict(base, changes=saved_changes)) if base.get("infer") is not False else None
        result["applied"] = result["applied"][len(saved_changes):]
        result["changed"] = diff_metrics(before, result["after"])
    else:
        result = WORKER.call("simulate", params)
    result["settingsApplied"] = {k: v for k, v in (("group", base.get("group")), ("minionSkill", base.get("minionSkill")), ("changes", saved_changes)) if v}
    return result


def diff_metrics(before, after):
    diff = {}
    for key, value in after.items():
        old = before.get(key)
        if isinstance(value, (int, float)) and isinstance(old, (int, float)) and value != old:
            diff[key] = {"before": old, "after": value, "change": round(value - old, 2),
                         "percent": round((value / old - 1) * 100, 1) if old else None}
    return diff


def tool_contributions(args):
    try:
        return library.run_contributions(args["build"], include_passives=args.get("includePassives", True),
                                         overrides={"group": args.get("group"), "minionSkill": args.get("minionSkill"),
                                                    "changes": args.get("changes") or [], "infer": args.get("infer"),
                                                    "minionCount": args.get("minionCount"), "summonRate": args.get("summonRate"),
                                                    "mercenary": args.get("mercenary"), "checkBuild": args.get("checkBuild")},
                                         save=not args.get("changes") and not args.get("minionSkill") and args.get("group") is None)
    except LookupError as e:
        raise ToolError(str(e))


def tool_full_analysis(args):
    import analysis
    try:
        result = analysis.analyse(args["build"], include_passives=args.get("includePassives", True))
    except LookupError as e:
        raise ToolError(str(e))
    with open(result["reportPath"], encoding="utf-8") as f:
        report = f.read()
    return {"reportPath": result["reportPath"], "questions": result["questions"], "report": report}


def tool_infer(args):
    xml, name, _, settings = resolve_build(args["build"])
    params = worker_params(args, xml, name, settings)
    return WORKER.call("infer", params)


def tool_save_settings(args):
    _, name, build_id, current = resolve_build(args["build"])
    if not build_id:
        raise ToolError("settings can only be saved for library builds")
    new = {"group": args.get("group", current.get("group")), "minionSkill": args.get("minionSkill", current.get("minionSkill")),
           "changes": args.get("changes", current.get("changes")), "summonRate": args.get("summonRate", current.get("summonRate")),
           "mercenary": args.get("mercenary", current.get("mercenary"))}
    saved = library.save_settings(build_id, new, args.get("note", current.get("note")))
    return {"build": name, "settings": saved, "note": args.get("note", current.get("note"))}


def tool_play_log(args):
    try:
        data = clientlog.load()
    except LookupError as e:
        raise ToolError(str(e))
    return clientlog.summarize(data, args.get("character"), args.get("since"), args.get("level"), args.get("top") or 10)


def filters_of(args):
    return {k: args.get(k) for k in library.FILTERS if args.get(k)}


HANDLERS = {
    "pob_list_builds": lambda a: library.query_search(filters_of(a)),
    "pob_build_summary": tool_build_summary,
    "pob_metrics": tool_metrics,
    "pob_simulate": tool_simulate,
    "pob_contributions": tool_contributions,
    "pob_damage_breakdown": lambda a: WORKER.call("damage_breakdown", worker_params(a, *resolve_build(a["build"])[:2], resolve_build(a["build"])[3])),
    "pob_config_sensitivity": lambda a: WORKER.call("config_sensitivity", worker_params(a, *resolve_build(a["build"])[:2], resolve_build(a["build"])[3])),
    "pob_full_analysis": tool_full_analysis,
    "pob_scenarios": lambda a: WORKER.call("scenarios", worker_params(a, *resolve_build(a["build"])[:2], resolve_build(a["build"])[3])),
    "pob_infer_conditions": tool_infer,
    "pob_save_build_settings": tool_save_settings,
    "pob_mercenaries": lambda a: WORKER.call("mercenaries", {"class": a.get("class")} if a.get("class") else {}),
    "pob_find_uniques": lambda a: WORKER.call("find_uniques", {k: a[k] for k in ("tags", "slot", "limit") if a.get(k) is not None}),
    "pob_find_passives": lambda a: WORKER.call("find_passives", {k: a[k] for k in ("tags", "types", "ascendancy", "limit") if a.get(k) is not None}),
    "pob_list_tags": lambda a: WORKER.call("list_tags", {}),
    "library_common": lambda a: library.query_common(filters_of(a), a.get("top") or 10),
    "library_item_usage": lambda a: library.query_item_usage(a["item"], a.get("top") or 10),
    "library_core_parts": lambda a: library.query_core_parts(filters_of(a), a.get("top") or 15),
    "play_log": tool_play_log,
    "sim_stats": lambda a: simlog.stats(a.get("kind"), a.get("skill"), a.get("ascendancy"), a.get("top") or 20)
                 if any(a.get(k) for k in ("kind", "skill", "ascendancy")) else simlog.summary(),
    "pob_mechanics": lambda a: WORKER.call("mechanics", {k: a[k] for k in ("id", "query") if a.get(k)}),
}


def handle(message):
    """Return the JSON-RPC response for one message, or None for notifications."""
    method = message.get("method")
    msg_id = message.get("id")
    if msg_id is None:
        return None  # notification, e.g. notifications/initialized
    if method == "initialize":
        version = (message.get("params") or {}).get("protocolVersion") or DEFAULT_PROTOCOL
        result = {"protocolVersion": version, "capabilities": {"tools": {"listChanged": False}},
                  "serverInfo": SERVER_INFO, "instructions": INSTRUCTIONS}
    elif method == "ping":
        result = {}
    elif method == "tools/list":
        result = {"tools": TOOLS}
    elif method == "tools/call":
        params = message.get("params") or {}
        name, args = params.get("name"), params.get("arguments") or {}
        if name not in HANDLERS:
            return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32602, "message": f"unknown tool '{name}'"}}
        try:
            data = HANDLERS[name](args)
            result = {"content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False)}], "isError": False}
        except (ToolError, WorkerError) as e:
            result = {"content": [{"type": "text", "text": str(e)}], "isError": True}
        except Exception as e:  # report, keep serving
            log(traceback.format_exc())
            result = {"content": [{"type": "text", "text": f"{type(e).__name__}: {e}"}], "isError": True}
    else:
        return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": f"method not found: {method}"}}
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def serve(stdin=sys.stdin, stdout=sys.stdout):
    for line in stdin:
        if not line.strip():
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError as e:
            stdout.write(json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(e)}}) + "\n")
            stdout.flush()
            continue
        response = handle(message)
        if response is not None:
            stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
            stdout.flush()


if __name__ == "__main__":
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    serve()
