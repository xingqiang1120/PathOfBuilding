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
import subprocess
import sys
import threading
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import library  # noqa: E402

SERVER_INFO = {"name": "path-of-building", "version": "0.1.0"}
DEFAULT_PROTOCOL = "2025-06-18"

INSTRUCTIONS = """Path of Building (PoB) for Path of Exile 1, run headless, plus a local library of saved builds.
- Numbers come from PoB's own calculation. Every build summary lists modifier lines PoB does NOT calculate
  ("coverage.unsupported") and the Config assumptions it relies on ("config"); mention them when they affect advice.
- For minion builds the DPS is per minion; the number of minions alive is not modelled.
- Use pob_simulate to check a suggestion before recommending it, and report the before/after numbers.
- Tags (pob_list_tags) classify items and passives, e.g. minion, phantasm, energyshield, fire."""

CHANGE_SCHEMA = {
    "type": "object",
    "description": "One change. Types: gem_replace {gem, with, group?, level?, quality?}; gem_add {group, gem, level?}; "
                   "gem_remove {gem, group?}; gem_level {gem, level?, quality?}; main_group {group}; "
                   "item_equip {slot, unique | raw}; item_remove {slot}; passive_add {node}; passive_remove {node}; "
                   "config_set {key, value}. group = socket group number or the name of a gem in it. "
                   "slot = PoB slot name, e.g. Helmet, Body Armour, Weapon 1, Ring 2, Flask 3.",
    "properties": {
        "type": {"type": "string", "enum": ["gem_replace", "gem_add", "gem_remove", "gem_level", "main_group", "item_equip",
                                            "item_remove", "passive_add", "passive_remove", "config_set"]},
        "gem": {"type": "string"}, "with": {"type": "string"}, "group": {"type": ["integer", "string"]},
        "level": {"type": "integer"}, "quality": {"type": "integer"}, "slot": {"type": "string"},
        "unique": {"type": "string"}, "raw": {"type": "string", "description": "Item text as copied from the game or PoB"},
        "node": {"type": ["string", "integer"], "description": "Passive name or node id"},
        "key": {"type": "string"}, "value": {},
    },
    "required": ["type"],
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
     "description": "Current key numbers of a build (DPS incl. minion DPS, life, ES, EHP, max hit taken per damage type, resistances, block, attributes).",
     "inputSchema": {"type": "object", "properties": {"build": BUILD_ARG, "group": {"type": ["integer", "string"], "description": "Socket group to treat as main skill (default: strongest)"}},
                     "required": ["build"]}},
    {"name": "pob_simulate",
     "description": "Apply changes to a copy of a build (gems, items, passives, config) and return the numbers before and after, "
                    "with every stat that changed. The saved build is never modified.",
     "inputSchema": {"type": "object", "properties": {"build": BUILD_ARG, "changes": {"type": "array", "items": CHANGE_SCHEMA},
                                                      "group": {"type": ["integer", "string"], "description": "Main skill group (default: strongest)"}},
                     "required": ["build", "changes"]}},
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


class Worker:
    """Persistent Path of Building process (tools/PobWorker.lua)."""

    def __init__(self):
        self.proc = None
        self.lock = threading.Lock()
        self.next_id = 0

    def start(self):
        cmd = [sys.executable, os.path.join(ROOT, "tools", "runlua.py"), os.path.join(ROOT, "tools", "PobWorker.lua")]
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                     text=True, encoding="utf-8", errors="replace", cwd=ROOT)
        for line in self.proc.stdout:
            if line.startswith("@@READY"):
                return
            if line.startswith("LUA ERROR"):
                break
        raise RuntimeError("Path of Building worker failed to start")

    def call(self, method, params):
        with self.lock:
            if self.proc is None or self.proc.poll() is not None:
                self.start()
            self.next_id += 1
            self.proc.stdin.write(json.dumps({"id": self.next_id, "method": method, "params": params}) + "\n")
            self.proc.stdin.flush()
            for line in self.proc.stdout:
                if line.startswith("@@RESP "):
                    answer = json.loads(line[7:])
                    if not answer.get("ok"):
                        raise ToolError(answer.get("error", "unknown error"))
                    return answer.get("result")
            self.proc = None
            raise RuntimeError("Path of Building worker stopped unexpectedly")


class ToolError(Exception):
    """An error the AI can act on (bad build name, unknown gem, ...)."""


WORKER = Worker()


def resolve_build(key):
    """Return (xml, name, library_id or None) for a library key or an .xml path."""
    if key.lower().endswith(".xml"):
        path = key if os.path.isabs(key) else os.path.join(ROOT, key)
        if not os.path.exists(path):
            raise ToolError(f"build file not found: {key}")
        with open(path, encoding="utf-8") as f:
            return f.read(), os.path.basename(path)[:-4], None
    db = library.connect()
    row = db.execute("SELECT * FROM builds WHERE id LIKE ? OR name LIKE ? ORDER BY name = ? DESC, added_at DESC",
                     (key + "%", f"%{key}%", key)).fetchone()
    if not row:
        raise ToolError(f"no library build matches '{key}' (use pob_list_builds)")
    raw = os.path.join(library.LIBRARY, "raw", row["id"] + ".xml")
    with open(raw, encoding="utf-8") as f:
        return f.read(), row["name"], row["id"]


def tool_build_summary(args):
    xml, name, build_id = resolve_build(args["build"])
    if build_id and not args.get("refresh"):
        path = os.path.join(library.LIBRARY, "summary", build_id + ".json")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                summary = json.load(f)
            summary.pop("tagInfo", None)
            return summary
    summary = WORKER.call("summary", {"xml": xml, "name": name})
    summary.pop("tagInfo", None)
    return summary


def tool_metrics(args):
    xml, name, _ = resolve_build(args["build"])
    params = {"xml": xml, "name": name}
    if args.get("group") is not None:
        params["group"] = args["group"]
    return WORKER.call("metrics", params)


def tool_simulate(args):
    xml, name, _ = resolve_build(args["build"])
    params = {"xml": xml, "name": name, "changes": args.get("changes") or []}
    if args.get("group") is not None:
        params["group"] = args["group"]
    return WORKER.call("simulate", params)


def filters_of(args):
    return {k: args.get(k) for k in library.FILTERS if args.get(k)}


HANDLERS = {
    "pob_list_builds": lambda a: library.query_search(filters_of(a)),
    "pob_build_summary": tool_build_summary,
    "pob_metrics": tool_metrics,
    "pob_simulate": tool_simulate,
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
        except ToolError as e:
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
