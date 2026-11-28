"""Market gear templates for the generator (v24): tools/data/gear_templates.json.

    python tools/gear_templates.py build     rebuild the file from the private data repo's market pool
    python tools/gear_templates.py show      print every template as PoB item text

The market pool (pob-lab-data/inputs/gear/market/intl-Covens/<date>-r2, -r3, -rB) holds, per slot and base type (or
per accessory variant), the 10 best listings under 10 chaos on the official trade site, sorted by the pool's own rule.
The generator wears the 5th of each (a mid-pack 10c item, not the best one); the other nine stay in the file as
candidates, for a build-around profile that prefers another one (v25). The file keeps only the items' lines, base,
item level and quality, the league and the date - never the seller.

Slots and groups (decision 2026-11-28, tools/TASKS.zh-TW.md T7):
  Body Armour: life + resistances, per base type (armour / evasion / energy_shield)
  Boots:       life + resistances + movement speed >= 25%, per base type
  Helmet, Gloves: life + resistances + accuracy, per base type
  Ring 1 / Ring 2: life + resistances + accuracy (5th and 6th, so the two rings differ); chaos_res kept for later
  Amulet:      life_res (life + resistances) or crit_multi (life + resistances + global crit multiplier)
  Belt:        life_res
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import labdata  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "gear_templates.json")
MARKET = os.path.join(labdata.DATA, "inputs", "gear", "market", "intl-Covens")
RANK = 5
# slot -> (round folder, pool file, {group key in this file: template key in the pool})
SOURCES = {
    "Body Armour": ("2026-11-28-r2", "chest", {"armour": "armour", "evasion": "evasion", "energy_shield": "energy_shield"}),
    "Helmet": ("2026-11-28-r3", "helmet", {"armour": "armour", "evasion": "evasion", "energy_shield": "energy_shield"}),
    "Gloves": ("2026-11-28-r3", "gloves", {"armour": "armour", "evasion": "evasion", "energy_shield": "energy_shield"}),
    "Boots": ("2026-11-28-r3", "boots", {"armour": "armour", "evasion": "evasion", "energy_shield": "energy_shield"}),
    "Ring 1": ("2026-11-28-rB", "ring", {"accuracy": "accuracy", "chaos_res": "chaos_res"}),
    "Ring 2": ("2026-11-28-rB", "ring", {"accuracy": "accuracy", "chaos_res": "chaos_res"}),
    "Amulet": ("2026-11-28-rB", "amulet", {"life_res": "life_res", "crit_multi": "crit_multi"}),
    "Belt": ("2026-11-28-rB", "belt", {"life_res": "life_res"}),
}
RANKS = {"Ring 2": RANK + 1}  # the second ring is the next listing, so the two rings are not the same item
PREFIX = {"crafted": "{crafted}", "fractured": "{fractured}"}


def pob_text(it):
    """The listing as PoB item text: implicits (and enchants) first, then the explicit lines; crafted and fractured
    lines carry PoB's tags; a 'Veiled' placeholder line is dropped (PoB cannot read it)."""
    implicit = [m["text"] for m in it["mods"] if m["type"] == "implicit"]
    enchant = ["{enchant}" + m["text"] for m in it["mods"] if m["type"] == "enchant"]
    explicit = [PREFIX.get(m["type"], "") + m["text"] for m in it["mods"] if m["type"] in ("explicit", "crafted", "fractured")]
    lines = ["Rarity: RARE", it["name"], it["base"]]
    if it.get("quality"):
        lines.append(f"Quality: {it['quality']}")
    lines += [f"Item Level: {it['item_level']}", f"Implicits: {len(implicit) + len(enchant)}", *enchant, *implicit, *explicit]
    return "\n".join(lines)


def listing(i, rank, n):
    props = i.get("properties", {})
    q = props.get("Quality", "")
    quality = int("".join(c for c in q if c.isdigit()) or 0) if q else 0
    it = {"name": i["name"], "base": i["base"], "item_level": int(i.get("item_level") or 86), "quality": quality,
          "mods": i["mods"], "pseudo": i.get("pseudo", {}), "defence_shown": i.get("defence_shown"), "price_chaos": (i.get("price") or {}).get("amount"),
          "rank": rank, "of": n}
    it["text"] = pob_text(it)
    return it


def entry(pool, key, rank, src):
    """The worn listing (rank) of one pool, plus every listing of the pool as candidates (v25: a build-around profile may
    prefer another one, e.g. the least lightning resistance for Doryani's Prototype)."""
    t = pool["templates"][key]
    best = t["best10"]
    it = dict(listing(best[min(rank, len(best)) - 1], min(rank, len(best)), len(best)),
              thresholds=t["thresholds"], key_mod=t.get("key_mod"), **{"from": src})
    it["candidates"] = [listing(x, k + 1, len(best)) for k, x in enumerate(best)]
    return it


def build():
    slots = {}
    for slot, (folder, part, groups) in SOURCES.items():
        path = os.path.join(MARKET, folder, f"{part}.json")
        with open(path, encoding="utf-8") as f:
            pool = json.load(f)
        slots[slot] = {g: entry(pool, k, RANKS.get(slot, RANK), f"{folder}/{part}.json") for g, k in groups.items()}
    data = {"_about": __doc__.strip().splitlines()[0] + " Built by tools/gear_templates.py from the private market pool; "
                      "item lines, base, item level, quality, league and date only - no seller.",
            "server": "intl", "league": "Covens", "date": "2026-11-28", "price_cap": "10 chaos", "rank": RANK,
            "rule": "Each pool is the 10 best listings under 10 chaos, scored life + elemental resistance (+ the slot's key mod); "
                    "the generator wears the 5th (Ring 2 the 6th).",
            "slots": slots}
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")
    return data


def load():
    with open(OUT, encoding="utf-8") as f:
        return json.load(f)


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "show"
    data = build() if cmd == "build" else load()
    for slot, groups in data["slots"].items():
        for g, it in groups.items():
            print(f"=== {slot} / {g} (#{it['rank']} of {it['of']}, {it['price_chaos']:g}c, {it['from']})")
            print(it["text"])
            print()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
