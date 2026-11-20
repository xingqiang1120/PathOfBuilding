"""Play log analysis from Path of Exile's own Client.txt.

The game writes logs/Client.txt next to the executable. It records, with timestamps, every area the game generates
(area id, monster level, seed), every area you enter, deaths and level-ups. This module turns it into map runs (time
in each map, portals used, deaths) so play can be compared with Path of Building's predictions. Reading this file is
the same thing many community tools do; nothing reads game memory or network traffic.

Chat and whispers are never kept: only the line patterns below are parsed, and tools/export_clientlog.ps1 (run on the
game PC) already drops chat before the file is copied.

    python tools/clientlog.py import <Client.txt or exported file> [--since 2026-11-01] [--character NAME]
    python tools/clientlog.py summary [--character NAME] [--since ...] [--level 83]
    python tools/clientlog.py templates      # system messages not understood yet (for a localized client)

Parsed logs are stored in library/playlogs/ (git-ignored, contains character names).
"""
import argparse
import datetime as dt
import json
import os
import re
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIBRARY = os.environ.get("POB_LIBRARY", os.path.join(ROOT, "library"))

LINE = re.compile(r"^(\d{4}/\d\d/\d\d \d\d:\d\d:\d\d) \d+ \S+ \[(\w+) Client \d+\] (.*)$")
GENERATING = re.compile(r'^Generating level (\d+) area "([^"]+)"(?: with seed (\d+))?')
SCENE = re.compile(r"^\[SCENE\] Set Source \[(.+)\]$")
LOG_OPEN = "***** LOG FILE OPENING *****"
# System messages start with ": ". English first; the Chinese forms are best guesses until confirmed from a real log
# ("templates" lists what was not recognised).
ENTERED = [re.compile(r"^: You have entered (.+)\.$"), re.compile(r"^: 你已進入[：:]\s*(.+?)。?$"),
           re.compile(r"^: 你已进入[：:]\s*(.+?)。?$")]
SLAIN = [re.compile(r"^: (\S+) has been slain\.$"), re.compile(r"^: (\S+) 已被殺死。?$"), re.compile(r"^: (\S+) 已死亡。?$"),
         re.compile(r"^: (\S+) 被杀死了。?$")]
LEVEL = [re.compile(r"^: (\S+) \(([^)]+)\) is now level (\d+)$"), re.compile(r"^: (\S+) [(（]([^)）]+)[)）] 現在等級為 (\d+)"),
         re.compile(r"^: (\S+) [(（]([^)）]+)[)）] 现在是 (\d+) 级")]
CHAT_PREFIX = tuple("@#$%&")
IDLE_CAP = 30 * 60  # seconds; a longer gap between events is treated as AFK or a closed game

TOWN = re.compile(r"town|Hideout|_Labyrinth_Airlock|KalguuranSettlement|Menagerie", re.I)


def area_kind(area_id):
    if area_id.startswith("Hideout") or "Hideout" in area_id:
        return "hideout"
    if area_id.startswith("Map"):
        return "map"  # before towns: "MapWorldsCrimsonTownship"
    if TOWN.search(area_id):
        return "town"
    return "other"


def first_match(patterns, text):
    for p in patterns:
        m = p.match(text)
        if m:
            return m
    return None


def mask(text):
    """Template of a message with names and numbers hidden, so unknown messages can be shared safely."""
    text = re.sub(r"\d+", "N", text)
    return re.sub(r"^: \S+", ": NAME", text)[:120]


def parse(lines, since=None):
    """Return {"instances": [...], "deaths": [...], "levels": [...], "unknown": {template: count}, "period": [first, last]}."""
    instances, deaths, levels, unknown = [], [], [], {}
    pending = None       # instance generated but not entered yet
    current = None       # instance we are in
    entered_at = None
    last_ts = None
    first_ts = None

    def close(until):
        nonlocal entered_at
        if current is not None and entered_at is not None and until is not None:
            current["seconds"] += min(max((until - entered_at).total_seconds(), 0), IDLE_CAP)
        entered_at = None

    def enter(name, ts):
        nonlocal current, pending, entered_at
        if current is not None and current.get("name") == name and entered_at is not None and pending is None:
            return  # the same entry reported twice ([SCENE] and "You have entered")
        close(ts)
        if pending is not None:
            inst, pending = pending, None
            inst["name"] = inst["name"] or name
        else:
            inst = next((i for i in reversed(instances) if i["name"] == name and i["kind"] not in ("town", "hideout")), None)
            if inst is None:
                inst = new_instance(None, None, None, ts)
                inst["name"] = name
                instances.append(inst)
        if inst is not current:
            inst["entries"] += 1
        current, entered_at = inst, ts

    def new_instance(area_id, level, seed, ts):
        return {"id": len(instances), "areaId": area_id, "kind": area_kind(area_id) if area_id else "other", "level": level, "seed": seed,
                "name": None, "start": ts.isoformat(sep=" "), "seconds": 0.0, "entries": 0, "deaths": 0}

    for raw in lines:
        raw = raw.rstrip("\r\n")
        if LOG_OPEN in raw:
            close(last_ts)
            current = pending = None
            continue
        m = LINE.match(raw)
        if not m:
            continue
        ts = dt.datetime.strptime(m.group(1), "%Y/%m/%d %H:%M:%S")
        if since and ts < since:
            continue
        msg = m.group(3)
        first_ts = first_ts or ts
        if last_ts and (ts - last_ts).total_seconds() > IDLE_CAP and entered_at is not None:
            close(last_ts)  # long silence: stop the clock at the last event, restart on this one
            entered_at = ts
        last_ts = ts

        g = GENERATING.match(msg)
        if g:
            pending = new_instance(g.group(2), int(g.group(1)), g.group(3), ts)
            instances.append(pending)
            continue
        s = SCENE.match(msg)
        if s:
            if s.group(1) != "(null)":
                enter(s.group(1), ts)
            continue
        if not msg.startswith(": "):
            continue
        body = msg[2:]
        if body.startswith(CHAT_PREFIX) or re.match(r"^(<[^>]*> )?\S+: ", body):
            continue  # chat or whisper: never kept
        e = first_match(ENTERED, msg)
        if e:
            enter(e.group(1), ts)
            continue
        d = first_match(SLAIN, msg)
        if d:
            where = current or {}
            if current is not None:
                current["deaths"] += 1
            deaths.append({"time": ts.isoformat(sep=" "), "character": d.group(1), "instance": where.get("id"), "area": where.get("name"),
                           "areaId": where.get("areaId"), "level": where.get("level"), "kind": where.get("kind")})
            continue
        lv = first_match(LEVEL, msg)
        if lv:
            levels.append({"time": ts.isoformat(sep=" "), "character": lv.group(1), "class": lv.group(2), "level": int(lv.group(3))})
            continue
        t = mask(msg)
        unknown[t] = unknown.get(t, 0) + 1
    close(last_ts)
    return {"instances": [i for i in instances if i["entries"] or i["deaths"]], "deaths": deaths, "levels": levels,
            "unknown": unknown, "period": [first_ts and first_ts.isoformat(sep=" "), last_ts and last_ts.isoformat(sep=" ")]}


def read_lines(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        yield from f


def store_dir():
    return os.path.join(LIBRARY, "playlogs")


def import_log(path, since=None):
    data = parse(read_lines(path), since)
    data["source"] = os.path.basename(path)
    os.makedirs(store_dir(), exist_ok=True)
    out = os.path.join(store_dir(), "latest.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    return data, out


def load(path=None):
    path = path or os.path.join(store_dir(), "latest.json")
    if not os.path.exists(path):
        raise LookupError("no play log imported yet: run tools/clientlog.py import <file>")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _minutes(seconds):
    return round(seconds / 60, 1)


def summarize(data, character=None, since=None, level=None, top=10):
    """Map runs, time per map and deaths, filtered by character (deaths), start time and area level."""
    since_s = since.isoformat(sep=" ") if isinstance(since, dt.datetime) else since
    characters = {}
    for lv in data["levels"]:
        characters[lv["character"]] = {"class": lv["class"], "level": lv["level"], "time": lv["time"]}
    if character is None and len(characters) == 1:
        character = next(iter(characters))

    def keep(item, key="start"):
        return (not since_s or item[key] >= since_s) and (level is None or item.get("level") == level)

    deaths = [d for d in data["deaths"] if keep(d, "time") and (character is None or d["character"] == character)]
    maps = [i for i in data["instances"] if i["kind"] == "map" and keep(i)]
    # deaths per instance for the chosen character only
    for m in maps:
        m["myDeaths"] = sum(1 for d in deaths if d["instance"] == m["id"])
    times = [m["seconds"] for m in maps if m["seconds"] > 0]
    by_level, by_map = {}, {}
    for m in maps:
        for table, key in ((by_level, m["level"]), (by_map, m["name"] or m["areaId"])):
            row = table.setdefault(key, {"runs": 0, "seconds": 0.0, "deaths": 0})
            row["runs"] += 1
            row["seconds"] += m["seconds"]
    for d in deaths:
        if d["kind"] == "map":
            by_level.setdefault(d["level"], {"runs": 0, "seconds": 0.0, "deaths": 0})["deaths"] += 1
            by_map.setdefault(d["area"] or d["areaId"], {"runs": 0, "seconds": 0.0, "deaths": 0})["deaths"] += 1

    def table(rows):
        return [{"key": k, "runs": r["runs"], "avgMinutes": _minutes(r["seconds"] / r["runs"]) if r["runs"] else None,
                 "deaths": r["deaths"]} for k, r in rows.items()]

    all_time = sum(i["seconds"] for i in data["instances"] if keep(i))
    kind_time = {}
    for i in data["instances"]:
        if keep(i):
            kind_time[i["kind"]] = kind_time.get(i["kind"], 0) + i["seconds"]
    return {
        "period": data["period"], "character": character, "characters": characters,
        "maps": {"runs": len(maps), "medianMinutes": _minutes(statistics.median(times)) if times else None,
                 "avgMinutes": _minutes(sum(times) / len(times)) if times else None,
                 "deaths": sum(1 for d in deaths if d["kind"] == "map"),
                 "deathsPerMap": round(sum(1 for d in deaths if d["kind"] == "map") / len(maps), 3) if maps else None,
                 "mapsWithDeath": sum(1 for m in maps if m["myDeaths"]),
                 "byLevel": sorted(table(by_level), key=lambda r: (r["key"] is None, r["key"] or 0)),
                 "mostDeaths": sorted((r for r in table(by_map) if r["deaths"]), key=lambda r: -r["deaths"])[:top],
                 "slowest": sorted(({"map": m["name"] or m["areaId"], "level": m["level"], "minutes": _minutes(m["seconds"]),
                                     "portals": m["entries"], "deaths": m["myDeaths"], "start": m["start"]} for m in maps),
                                   key=lambda r: -r["minutes"])[:top]},
        "timeShare": {k: round(v / all_time, 3) for k, v in sorted(kind_time.items(), key=lambda kv: -kv[1])} if all_time else {},
        "deaths": deaths[-top:],
        "notes": ["Time in a map stops at the next area you enter (hideout, town or another map); a gap of more than "
                  f"{IDLE_CAP // 60} min between log lines is treated as AFK.",
                  "Deaths are matched to the area you were in. Client.txt does not record what killed you or the hit size."],
        "unrecognisedMessages": sum(data["unknown"].values()),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("import")
    p.add_argument("path")
    p.add_argument("--since")
    for name in ("summary", "templates"):
        q = sub.add_parser(name)
        q.add_argument("--character")
        q.add_argument("--since")
        q.add_argument("--level", type=int)
    args = ap.parse_args(argv)
    since = dt.datetime.fromisoformat(args.since) if getattr(args, "since", None) else None
    if args.cmd == "import":
        data, out = import_log(args.path, since)
        print(f"imported {len(data['instances'])} areas, {len(data['deaths'])} deaths, {len(data['levels'])} level-ups "
              f"({data['period'][0]} .. {data['period'][1]}) -> {out}")
        if data["unknown"]:
            print(f"{sum(data['unknown'].values())} system messages not recognised (see: clientlog.py templates)")
        return
    data = load()
    if args.cmd == "templates":
        for t, n in sorted(data["unknown"].items(), key=lambda kv: -kv[1])[:60]:
            print(f"{n:6d}  {t}")
        return
    json.dump(summarize(data, args.character, since, args.level), sys.stdout, ensure_ascii=False, indent=1)
    print()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
