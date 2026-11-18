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
- Use pob_simulate to check a suggestion before recommending it, and report the before/after numbers.
- Tags (pob_list_tags) classify items and passives, e.g. minion, phantasm, energyshield, fire."""

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
    "infer": {"type": "boolean", "description": "Estimate Config values the build leaves at 0, e.g. withered stacks from wither chance x hits per second (default true)"},
    "minionCount": {"type": "integer", "description": "Minions alive for inference (default: the minion limit, i.e. steady state)"},
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
    {"name": "pob_save_build_settings",
     "description": "Save play-verified settings for a library build so every later analysis uses them: main group, the skill its minions "
                    "really use, and Config changes (e.g. withered stacks). Only save what the user confirmed. Omitted fields keep their value.",
     "inputSchema": {"type": "object", "properties": {"build": BUILD_ARG, "group": MAIN_PROPS["group"], "minionSkill": MAIN_PROPS["minionSkill"],
                                                      "changes": {"type": "array", "items": CHANGE_SCHEMA}, "note": {"type": "string"}},
                     "required": ["build"]}},
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
                 "infer": args.get("infer"), "minionCount": args.get("minionCount")}
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
                                                                          "infer": args.get("infer"), "minionCount": args.get("minionCount")})
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
                                                    "minionCount": args.get("minionCount")},
                                         save=not args.get("changes") and not args.get("minionSkill") and args.get("group") is None)
    except LookupError as e:
        raise ToolError(str(e))


def tool_infer(args):
    xml, name, _, settings = resolve_build(args["build"])
    params = worker_params(args, xml, name, settings)
    return WORKER.call("infer", params)


def tool_save_settings(args):
    _, name, build_id, current = resolve_build(args["build"])
    if not build_id:
        raise ToolError("settings can only be saved for library builds")
    new = {"group": args.get("group", current.get("group")), "minionSkill": args.get("minionSkill", current.get("minionSkill")),
           "changes": args.get("changes", current.get("changes"))}
    saved = library.save_settings(build_id, new, args.get("note", current.get("note")))
    return {"build": name, "settings": saved, "note": args.get("note", current.get("note"))}


def filters_of(args):
    return {k: args.get(k) for k in library.FILTERS if args.get(k)}


HANDLERS = {
    "pob_list_builds": lambda a: library.query_search(filters_of(a)),
    "pob_build_summary": tool_build_summary,
    "pob_metrics": tool_metrics,
    "pob_simulate": tool_simulate,
    "pob_contributions": tool_contributions,
    "pob_infer_conditions": tool_infer,
    "pob_save_build_settings": tool_save_settings,
    "pob_find_uniques": lambda a: WORKER.call("find_uniques", {k: a[k] for k in ("tags", "slot", "limit") if a.get(k) is not None}),
    "pob_find_passives": lambda a: WORKER.call("find_passives", {k: a[k] for k in ("tags", "types", "ascendancy", "limit") if a.get(k) is not None}),
    "pob_list_tags": lambda a: WORKER.call("list_tags", {}),
    "library_common": lambda a: library.query_common(filters_of(a), a.get("top") or 10),
    "library_item_usage": lambda a: library.query_item_usage(a["item"], a.get("top") or 10),
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
