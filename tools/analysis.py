"""Build analysis pipeline: inbox intake, full analysis, reports and questions for the player.

    python tools/library.py inbox            analyse every build saved in src/Builds/inbox, then move it to src/Builds/done
    python tools/library.py report <build>   full analysis of one library build

Per build: PoB numbers with and without inferred conditions, the damage formula from PoB's own breakdown,
leave-one-out contributions (items, supports, notables), every modifier line, every Config assumption the
author switched on, unsupported modifiers, and the questions only someone who plays it can answer.

Notes written in PoB's Notes tab are read. Recognised lines (Chinese or English keys, ":" or "："):
    來源 / source:          where the build comes from
    目的 / purpose:         what to look at
    召喚物技能 / minion skill: the skill the minions really use (saved as a verified setting)
    主技能 / main skill:    socket group number or a gem name in it (saved as a verified setting)
    已知 / known:           what is already known from play
Reports go to library/reports/ (git-ignored with the rest of library/).
"""
import datetime
import json
import os
import re
import shutil
import xml.etree.ElementTree as ET

import library
from pob_worker import WORKER

ROOT = library.ROOT
INBOX = os.path.join(ROOT, "src", "Builds", "inbox")
DONE = os.path.join(ROOT, "src", "Builds", "done")

NOTE_KEYS = {
    "source": ("來源", "来源", "source"),
    "purpose": ("目的", "purpose", "goal"),
    "minionSkill": ("召喚物技能", "召唤物技能", "minion skill"),
    "mainSkill": ("主技能", "main skill", "main group"),
    "known": ("已知", "known"),
}


def reports_dir():
    path = os.path.join(library.LIBRARY, "reports")
    os.makedirs(path, exist_ok=True)
    os.makedirs(os.path.join(library.LIBRARY, "analysis"), exist_ok=True)
    return path


def parse_notes(xml_text):
    """Return ({key: value}, full text) from the build's Notes tab."""
    try:
        root = ET.fromstring(xml_text.encode("utf-8"))
    except ET.ParseError:
        return {}, ""
    node = root.find("Notes")
    text = (node.text or "") if node is not None else ""
    text = re.sub(r"\^x[0-9A-Fa-f]{6}|\^\d", "", text).strip()
    fields = {}
    for line in text.splitlines():
        m = re.match(r"\s*([^:：]+?)\s*[:：]\s*(.+)$", line)
        if not m:
            continue
        label, value = m.group(1).strip().lower(), m.group(2).strip()
        for key, names in NOTE_KEYS.items():
            if label in names and key not in fields:
                fields[key] = value
    return fields, text


def cell(text):
    """Make text safe for one Markdown table cell."""
    return str(text).replace("\n", " ").replace("|", "\\|")


def pct(value):
    return "-" if value is None else f"{value:+.1f}%"


def num(value):
    return "-" if value is None else f"{value:,.0f}"


def main_dps(m):
    return max(m.get("playerDPS") or 0, m.get("minionDPS") or 0)


def save_mod_rows(build_id, settings_applied, parts):
    db = library.connect()
    now = datetime.datetime.now().isoformat(timespec="seconds")
    db.execute("DELETE FROM contributions WHERE build_id = ? AND kind = 'mod'", (build_id,))
    for p in parts:
        role = "core damage" if (p.get("dpsPct") or 0) <= -10 else "damage" if (p.get("dpsPct") or 0) <= -2 else \
            "core defence" if (p.get("ehpPct") or 0) <= -10 else "defence" if (p.get("ehpPct") or 0) <= -2 else "no measurable effect"
        db.execute("INSERT INTO contributions VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                   (build_id, now, json.dumps(settings_applied, ensure_ascii=False), "mod", f"{p['item'].split(',')[0]}: {p['line']}",
                    p["slot"], p.get("dpsPct"), p.get("ehpPct"), None, role, 0, p.get("error")))
    db.commit()


def make_questions(result, summary, notes):
    """What the tools cannot know: answers turn into verified settings or knowledge base facts."""
    questions = []
    metrics = result["metrics"]
    options = result.get("minionSkillOptions") or []
    settings = result.get("settings") or {}
    if len(options) > 1 and not settings.get("minionSkill"):
        listing = ", ".join(f"{o['skill']} ({num(o['dps'])})" for o in options)
        questions.append(f"召喚物有多個技能：{listing}。目前用 {metrics.get('minionSkill')} 計算，實際上牠們用哪一個？")
    for inf in metrics.get("inferred") or []:
        if inf.get("applied"):
            needed = inf.get("minionsNeededForMax")
            extra = f"（只要 {needed} 隻就能疊滿）" if needed else ""
            questions.append(f"自動推算 {inf['label']} = {inf['value']}{extra}，假設：{'；'.join(inf.get('assumptions') or [])}。符合實際嗎？")
    for p in (result.get("config") or {}).get("parts", []):
        if p["key"] != "enemyIsBoss" and (abs(p["dpsPct"]) >= 5 or abs(p["ehpPct"]) >= 5):
            questions.append(f"作者假設 {p['key']} = {p['value']}（關掉後 DPS {pct(p['dpsPct'])}、EHP {pct(p['ehpPct'])}）。實戰中能一直維持嗎？")
    functional = [p for p in result["contributions"]["parts"] if (p.get("role") or "").startswith("functional")]
    if functional:
        names = "、".join(p["name"] for p in functional[:5])
        questions.append(f"PoB 量不出這些零件的效果：{names}。它們在這個流派裡的作用是什麼？")
    unsupported = [e for e in (summary.get("coverage") or {}).get("unsupported", []) if e.get("impact") in ("offence", "defence")]
    if unsupported:
        lines = "；".join(f"{e['source']}：{e['line']}" for e in unsupported[:5])
        questions.append(f"這些詞綴 PoB 不計算（共 {len(unsupported)} 行）：{lines}。哪些對這個流派重要？")
    return questions


def analyse(key, include_passives=True):
    xml_text, name, build_id = library.resolve(key)
    settings = library.get_settings(build_id)
    params = library.apply_settings({"xml": xml_text, "name": name}, settings)
    result = {"build": name, "buildId": build_id, "settings": settings,
              "analysedAt": datetime.datetime.now().isoformat(timespec="seconds")}
    result["metrics"] = WORKER.call("metrics", params)
    result["metricsWithoutInference"] = WORKER.call("metrics", dict(params, infer=False))
    skills = result["metrics"].get("minionSkills") or []
    if len(skills) > 1:
        result["minionSkillOptions"] = [{"skill": s, "dps": WORKER.call("metrics", dict(params, minionSkill=s)).get("minionDPS")}
                                        for s in skills]
    result["breakdown"] = WORKER.call("damage_breakdown", params)
    result["contributions"] = library.run_contributions(build_id or key, include_passives=include_passives)
    result["mods"] = WORKER.call("mod_contributions", params)
    if build_id:
        save_mod_rows(build_id, result["contributions"].get("settingsApplied"), result["mods"]["parts"])
    result["config"] = WORKER.call("config_sensitivity", params)
    summary = {}
    if build_id:
        with open(os.path.join(library.LIBRARY, "summary", build_id + ".json"), encoding="utf-8") as f:
            summary = json.load(f)
    notes, _ = parse_notes(xml_text)
    result["notes"] = notes
    result["questions"] = make_questions(result, summary, notes)
    result["unsupported"] = [e for e in (summary.get("coverage") or {}).get("unsupported", []) if e.get("impact") in ("offence", "defence")]
    result["character"] = summary.get("character", {})
    reports_dir()
    if build_id:
        with open(os.path.join(library.LIBRARY, "analysis", build_id + ".json"), "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=1)
    path = os.path.join(reports_dir(), safe_name(name) + ".md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(report_markdown(result))
    result["reportPath"] = path
    return result


def safe_name(name):
    return re.sub(r"[^\w\-]+", "_", name).strip("_")[:80] or "build"


def report_markdown(r):
    m, raw = r["metrics"], r["metricsWithoutInference"]
    bd = r["breakdown"]
    ch = r.get("character") or {}
    notes = r.get("notes") or {}
    parts = r["contributions"]["parts"]
    damage = [p for p in parts if (p.get("dpsPct") or 0) <= -2 and not (p.get("role") or "").startswith("tree hub")][:8]
    defence = sorted([p for p in parts if (p.get("ehpPct") or 0) <= -2 and not (p.get("role") or "").startswith("tree hub")],
                     key=lambda p: p["ehpPct"])[:8]
    functional = [p for p in parts if (p.get("role") or "").startswith("functional") or p.get("alsoFunctional")][:8]
    unit = "每隻召喚物 " if bd.get("actor") == "minion" else ""
    lines = [f"# {r['build']}", ""]
    lines.append(f"{ch.get('class', '?')} / {ch.get('ascendancy', '?')} · 等級 {ch.get('level', '?')} · 分析時間 {r['analysedAt']}")
    for key, label in (("source", "來源"), ("purpose", "目的"), ("known", "已知")):
        if notes.get(key):
            lines.append(f"- **{label}**：{notes[key]}")
    lines += ["", "## 一句話總結", ""]
    top_d = damage[0]["name"] if damage else "-"
    top_e = defence[0]["name"] if defence else "-"
    change = (main_dps(m) / main_dps(raw) - 1) * 100 if main_dps(raw) else 0
    lines.append(f"{bd.get('mainSkill')}：{unit}DPS **{num(main_dps(m))}**（PoB 原值 {num(main_dps(raw))}，推算條件後 {change:+.0f}%）。"
                 f"最大傷害來源 **{top_d}**，最大防禦來源 **{top_e}**。")
    lines += ["", "## 數字", "", "| 項目 | 數值 |", "|---|---|"]
    lines.append(f"| DPS（PoB 原值 → 推算後） | {num(main_dps(raw))} → {num(main_dps(m))} |")
    for k, label in (("Life", "生命"), ("EnergyShield", "能量護盾"), ("TotalEHP", "EHP"), ("PhysicalMaximumHitTaken", "物理最大承受"),
                     ("ChaosMaximumHitTaken", "混沌最大承受"), ("EffectiveBlockChance", "攻擊格擋 %"), ("EffectiveSpellBlockChance", "法術格擋 %")):
        if m.get(k) is not None:
            lines.append(f"| {label} | {num(m[k])} |")
    lines.append(f"| 抗性 火/冰/電/混 | {m.get('FireResist')}/{m.get('ColdResist')}/{m.get('LightningResist')}/{m.get('ChaosResist')} |")
    for inf in m.get("inferred") or []:
        lines.append(f"| 推算：{inf['label']} | {inf['value']}（估計 {inf['estimate']}，{'已套用' if inf.get('applied') else '未套用：' + str(inf.get('skipped'))}） |")
    lines += ["", "## 傷害公式（取自 PoB 的計算過程）", ""]
    lines.append(f"技能：{bd.get('mainSkill')}" + (f" → 召喚物技能 {bd.get('skill')}" if bd.get('actor') == 'minion' else "")
                 + (f"（{bd['weapon']}）" if bd.get('weapon') else ""))
    lines += ["", "| 傷害類型 | 佔比 | 基礎 | 增加 | 更多 | 轉換 | 敵人減傷 |", "|---|---|---|---|---|---|---|"]
    for dt in bd.get("damageTypes", []):
        for row in dt["rows"]:
            if row.get("base"):
                lines.append(f"| {dt['type']}（來自 {row['from']}） | {dt['portionPercent']}% | {row['base']} | x{row.get('increased') or 1} | "
                             f"x{row.get('more') or 1} | {row.get('convertedTo') or row.get('gainedAs') or '-'} | {dt['enemyMitigation'].get('value') or '-'} |")
    lines += ["", f"- 每秒次數：{bd['speed']['value']}（{' '.join(bd['speed']['lines'])}）",
              f"- 命中率 {bd['hitChance']}%，暴擊率 {bd['crit']['chance']}%，暴擊傷害 x{bd['crit']['multiplier']}，暴擊效果 x{bd['crit']['effect']}",
              f"- 平均單次命中 {num(bd['averageHit'])}，命中 DPS {num(bd['hitDPS'])}" + (f"，持續傷害 {bd['dot']}" if bd.get("dot") else "")]
    for dt in bd.get("damageTypes", []):
        if dt["enemyMitigation"].get("lines"):
            lines.append(f"- {dt['type']} 敵人減傷：{'；'.join(dt['enemyMitigation']['lines'])}")
    def table(title, rows, metric):
        out = ["", f"## {title}", "", "| 零件 | 類型 | DPS | EHP | 角色 |", "|---|---|---|---|---|"]
        for p in rows:
            out.append(f"| {cell(p['name'])} | {p['kind']} | {pct(p.get('dpsPct'))} | {pct(p.get('ehpPct'))} | {p.get('role')}{' / functional' if p.get('alsoFunctional') else ''} |")
        return out if rows else []
    lines += table("核心傷害零件（單獨拿掉時的變化）", damage, "dpsPct")
    lines += table("核心防禦零件", defence, "ehpPct")
    lines += table("功能性零件（PoB 量不出效果）", functional, "dpsPct")
    mods = r["mods"]["parts"]
    top_mod_d = [p for p in mods if (p.get("dpsPct") or 0) <= -1][:12]
    top_mod_e = sorted([p for p in mods if (p.get("ehpPct") or 0) <= -1], key=lambda p: p["ehpPct"])[:12]
    if top_mod_d or top_mod_e:
        lines += ["", "## 影響最大的詞綴（單獨拿掉一行）", "", "| 部位 | 詞綴 | DPS | EHP |", "|---|---|---|---|"]
        for p in top_mod_d + [p for p in top_mod_e if p not in top_mod_d]:
            lines.append(f"| {p['slot']} | {cell(p['line'])} | {pct(p.get('dpsPct'))} | {pct(p.get('ehpPct'))} |")
    cfg = [p for p in (r.get("config") or {}).get("parts", []) if abs(p["dpsPct"]) >= 1 or abs(p["ehpPct"]) >= 1]
    if cfg:
        lines += ["", "## 作者的 Config 假設（關掉後的變化）", "", "| 設定 | 作者的值 | DPS | EHP |", "|---|---|---|---|"]
        for p in cfg:
            lines.append(f"| {p['key']} | {p['value']} | {pct(p['dpsPct'])} | {pct(p['ehpPct'])} |")
    if r.get("unsupported"):
        lines += ["", "## PoB 不計算的詞綴", ""]
        lines += [f"- {e['source']}：{cell(e['line'])}（{e.get('impact')}）" for e in r["unsupported"]]
    lines += ["", "## ❓ 需要你確認", ""]
    lines += [f"{i}. {q}" for i, q in enumerate(r["questions"], 1)] or ["（沒有）"]
    return "\n".join(lines) + "\n"


def batch_report(results):
    """Cross-build view of one inbox run, plus what these builds rely on that your own builds do not use."""
    ids = [r["buildId"] for r in results if r.get("buildId")]
    lines = [f"# 批次分析 {datetime.datetime.now():%Y-%m-%d %H:%M}", "", "| 流派 | 昇華 | 技能 | DPS（原值 → 推算） | EHP | 問題數 | 報告 |", "|---|---|---|---|---|---|---|"]
    for r in results:
        m, raw = r["metrics"], r["metricsWithoutInference"]
        lines.append(f"| {r['build']} | {(r.get('character') or {}).get('ascendancy', '-')} | {r['breakdown'].get('skill')} | "
                     f"{num(main_dps(raw))} → {num(main_dps(m))} | {num(m.get('TotalEHP'))} | {len(r['questions'])} | {os.path.basename(r['reportPath'])} |")
    if ids:
        db = library.connect()
        marks = ",".join("?" * len(ids))
        rows = db.execute(f"""SELECT kind, name, COUNT(DISTINCT build_id) n, AVG(dps_pct) d FROM contributions
                              WHERE build_id IN ({marks}) AND dps_pct <= -10 AND role NOT LIKE 'tree hub%' AND kind != 'mod'
                              GROUP BY kind, name ORDER BY n DESC, d LIMIT 20""", ids).fetchall()
        if rows:
            lines += ["", "## 這批流派的核心傷害零件", "", "| 零件 | 類型 | 出現在幾個流派 | 平均 DPS |", "|---|---|---|---|"]
            lines += [f"| {r['name']} | {r['kind']} | {r['n']} | {r['d']:+.1f}% |" for r in rows]
        mine = [r[0] for r in db.execute("SELECT DISTINCT build_id FROM build_tags WHERE tag IN ('my-build', 'mine')")]
        if mine:
            mine_marks = ",".join("?" * len(mine))
            used = {r[0] for r in db.execute(f"SELECT DISTINCT name FROM contributions WHERE build_id IN ({mine_marks})", mine)}
            missing = [r for r in rows if r["name"] not in used] if rows else []
            if missing:
                lines += ["", "## 這批流派依賴、但你的角色沒用到的", ""]
                lines += [f"- {r['name']}（{r['kind']}，{r['n']} 個流派，平均 {r['d']:+.1f}%）" for r in missing]
    path = os.path.join(reports_dir(), f"batch-{datetime.datetime.now():%Y%m%d-%H%M}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return path


def process_inbox(folder=INBOX, done=DONE, include_passives=True):
    os.makedirs(folder, exist_ok=True)
    files = sorted(f for f in os.listdir(folder) if f.lower().endswith(".xml"))
    if not files:
        print(f"inbox is empty: {folder}")
        return []
    entries = []
    for fname in files:
        with open(os.path.join(folder, fname), encoding="utf-8") as f:
            xml_text = f.read()
        notes, text = parse_notes(xml_text)
        entries.append((xml_text, {"name": fname[:-4], "source": notes.get("source") or "inbox",
                                   "note": notes.get("purpose") or (text[:200] if text else None), "tags": ["inbox"]}, notes, fname))
    ids = library.add_builds([(x, meta) for x, meta, _, _ in entries])
    results = []
    for build_id, (_, meta, notes, fname) in zip(ids, entries):
        settings = library.get_settings(build_id)
        changed = False
        if notes.get("minionSkill"):
            settings["minionSkill"], changed = notes["minionSkill"], True
        if notes.get("mainSkill"):
            value = notes["mainSkill"]
            settings["group"], changed = (int(value) if value.isdigit() else value), True
        if changed:
            library.save_settings(build_id, settings, settings.get("note") or "from PoB notes")
        print(f"analysing {meta['name']} ...")
        try:
            result = analyse(build_id, include_passives=include_passives)
        except Exception as e:  # keep going with the rest of the batch
            print(f"  failed: {e}")
            continue
        results.append(result)
        print(f"  report: {result['reportPath']}  ({len(result['questions'])} question(s))")
        os.makedirs(done, exist_ok=True)
        shutil.move(os.path.join(folder, fname), os.path.join(done, fname))
    if results:
        print(f"batch report: {batch_report(results)}")
    return results
