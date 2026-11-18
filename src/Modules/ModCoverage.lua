-- Path of Building
--
-- Module: Mod Coverage
-- Reports which modifier lines Path of Building understands, maps the ones it does not to official
-- game stat ids (via Data/StatDescriptions/stat_descriptions.lua), and estimates whether a missing
-- line matters for the numbers (offence / defence) or not (utility / cosmetic).
--
-- Designed to be consumed by people (Markdown report) and by tools / AI (JSON entries).
--
local pairs = pairs
local ipairs = ipairs
local type = type
local t_insert = table.insert
local t_sort = table.sort

modCoverage = { }

-- Stat description index

local statIndex

local function escapePattern(str)
	return (str:gsub("([%^%$%(%)%%%.%[%]%*%+%-%?])", "%%%1"))
end

---Normalise a display line for matching: lower case, ranges "(10-20)" collapsed to their minimum.
function modCoverage.NormaliseLine(line)
	return (line:lower():gsub("%(([%-%d%.]+)%-[%-%d%.]+%)", "%1"):gsub("^%s+", ""):gsub("%s+$", ""))
end

---Build (once) the index from description text templates to stat ids.
function modCoverage.GetStatIndex()
	if statIndex then
		return statIndex
	end
	statIndex = { buckets = { }, count = 0 }
	local descriptions = LoadModule("Data/StatDescriptions/stat_descriptions")
	for _, entry in ipairs(descriptions) do
		if type(entry) == "table" and entry.stats then
			for _, lang in ipairs(entry) do
				if type(lang) == "table" then
					for _, variant in ipairs(lang) do
						if type(variant) == "table" and variant.text and not variant.text:find("\n") then
							local text = variant.text:lower()
							local pattern = "^" .. escapePattern(text):gsub("{%d*[^}]*}", "[%%+%%-]?[%%d%%.]+") .. "$"
							-- Bucket by the first plain word so lookups only test a few templates
							local key = text:gsub("{[^}]*}", " "):match("(%a%a+)")
							if key then
								statIndex.buckets[key] = statIndex.buckets[key] or { }
								t_insert(statIndex.buckets[key], { pattern = pattern, stats = entry.stats })
								statIndex.count = statIndex.count + 1
							end
						end
					end
				end
			end
		end
	end
	return statIndex
end

---Find the official stat ids for a display line, or nil.
---@return string[]?
function modCoverage.FindStatIds(line)
	local index = modCoverage.GetStatIndex()
	local norm = modCoverage.NormaliseLine(line)
	local tried = { }
	for word in norm:gmatch("(%a%a+)") do
		if not tried[word] then
			tried[word] = true
			for _, template in ipairs(index.buckets[word] or { }) do
				if norm:match(template.pattern) then
					return template.stats
				end
			end
		end
	end
end

-- Impact estimation

-- Ordered: the first matching group wins. Patterns are tested on "<line> <stat ids>" in lower case.
local impactRules = {
	{ impact = "cosmetic", patterns = { "footprint", "hoofprint", "portal", "effect_unique_", "_mtx", "cosmetic", "gore" } },
	-- Reflected damage is not modelled by Path of Building's damage numbers
	{ impact = "utility", patterns = { "reflect" } },
	{ impact = "defence", patterns = { "^remove", "damage taken", "damage from", "taken as", "you take", "on you%f[^%w]", "inflicted on you",
		"cannot be stunned", "stun threshold", "^you cannot", "to be ", "resist", "armour", "evasion", "energy shield", "block",
		"suppress", "maximum life", "life regen", "regenerate", "recover", "recoup", "leech", "fortif", "guard", "ward", "avoid",
		"ailment immunity", "aegis", "petrified", "life when", "mana when", "of life", "endurance charge" } },
	{ impact = "offence", patterns = { "damage", "critical", "attack speed", "cast speed", "penetrat", "accuracy", "projectile",
		"area of effect", "skill effect duration", "impale", "ignite", "bleed", "poison", "shock", "freeze", "chill", "exposure",
		"curse", "hex", "wither", "more ", "power charge", "frenzy charge", "to hit", "on hit", "explode", "minion", "totem",
		"trap", "mine", "brand", "aura", "trigger", "cooldown", "skills", "gem" } },
	{ impact = "utility", patterns = { "" } },
}

---Estimate the impact of a line on Path of Building's numbers.
---@return "offence"|"defence"|"utility"|"cosmetic"
function modCoverage.EstimateImpact(line, statIds)
	local text = line:lower() .. " " .. table.concat(statIds or { }, " "):lower()
	for _, group in ipairs(impactRules) do
		for _, pattern in ipairs(group.patterns) do
			if text:find(pattern) then
				return group.impact
			end
		end
	end
	return "utility"
end

---Classify one modifier line.
---@param line string @Display text
---@param modList table? @Parsed mods, if any
---@param extra any @Unparsed remainder reported by the mod parser
---@return table @{ line, status = "supported"|"unsupported", statIds, impact }
function modCoverage.ClassifyLine(line, modList, extra)
	local supported = modList ~= nil and modList[1] ~= nil and not extra
	local entry = { line = line, status = supported and "supported" or "unsupported" }
	if not supported then
		entry.statIds = modCoverage.FindStatIds(line)
		entry.impact = modCoverage.EstimateImpact(line, entry.statIds)
	end
	return entry
end

-- Scanners. Each returns a list of entries:
-- { kind = "unique"|"node", source = <name>, detail = <slot/type/ascendancy>, line, status, statIds?, impact? }

local itemLineGroups = { "enchantModLines", "implicitModLines", "explicitModLines", "crucibleModLines" }

local function scanItem(item, entries, kind, detail)
	for _, group in ipairs(itemLineGroups) do
		for _, modLine in ipairs(item[group] or { }) do
			if not modLine.disabled and (not item.CheckModLineVariant or item:CheckModLineVariant(modLine)) then
				local entry = modCoverage.ClassifyLine(modLine.line, modLine.modList, modLine.extra)
				entry.kind = kind
				entry.source = item.title or item.name
				entry.detail = detail or item.type
				t_insert(entries, entry)
			end
		end
	end
end

local function scanNode(node, entries)
	for index, line in ipairs(node.sd or { }) do
		local mods = node.mods and node.mods[index]
		if mods and not mods.combined then
			local entry = modCoverage.ClassifyLine(line, mods.list, mods.extra)
			entry.kind = "node"
			entry.source = node.dn
			entry.nodeId = node.id
			entry.detail = node.ascendancyName or node.type
			t_insert(entries, entry)
		end
	end
end

local function sortEntries(entries)
	t_sort(entries, function(a, b)
		if a.kind ~= b.kind then return a.kind < b.kind end
		if a.source ~= b.source then return a.source < b.source end
		return a.line < b.line
	end)
	return entries
end

---Scan all unique items (current variants).
function modCoverage.ScanUniques(uniqueDB)
	local entries = { }
	for _, item in pairs((uniqueDB or main.uniqueDB).list) do
		scanItem(item, entries, "unique")
	end
	return sortEntries(entries)
end

---Scan every node of a passive tree.
function modCoverage.ScanTree(tree)
	local entries = { }
	for _, node in pairs(tree.nodes) do
		if node.type ~= "ClassStart" and node.type ~= "AscendClassStart" then
			scanNode(node, entries)
		end
	end
	return sortEntries(entries)
end

---Scan what a loaded build actually uses: equipped items (active item set) and allocated nodes.
function modCoverage.ScanBuild(build)
	local entries = { }
	local itemsTab = build.itemsTab
	local seen = { }
	for slotName, slot in pairs(itemsTab.activeItemSet or { }) do
		if type(slot) == "table" and slot.selItemId and slot.selItemId ~= 0 then
			local item = itemsTab.items[slot.selItemId]
			if item and not seen[item] then
				seen[item] = true
				scanItem(item, entries, "item", slotName)
			end
		end
	end
	for _, node in pairs(build.spec.allocNodes) do
		if node.type ~= "ClassStart" and node.type ~= "AscendClassStart" then
			scanNode(node, entries)
		end
	end
	return sortEntries(entries)
end

-- Summaries and diffs

---Counts by kind, status and impact.
function modCoverage.Summarize(entries)
	local summary = { }
	for _, entry in ipairs(entries) do
		local s = summary[entry.kind] or { lines = 0, supported = 0, unsupported = 0, mapped = 0, impact = { }, sources = { }, sourcesWithGap = { } }
		summary[entry.kind] = s
		s.lines = s.lines + 1
		s.sources[entry.source] = true
		if entry.status == "supported" then
			s.supported = s.supported + 1
		else
			s.unsupported = s.unsupported + 1
			s.sourcesWithGap[entry.source] = true
			if entry.statIds then
				s.mapped = s.mapped + 1
			end
			s.impact[entry.impact] = (s.impact[entry.impact] or 0) + 1
		end
	end
	for _, s in pairs(summary) do
		local n, g = 0, 0
		for _ in pairs(s.sources) do n = n + 1 end
		for _ in pairs(s.sourcesWithGap) do g = g + 1 end
		s.sources, s.sourcesWithGap = n, g
	end
	return summary
end

local function entryKey(entry)
	return entry.kind .. "|" .. entry.source .. "|" .. entry.line
end

---Compare two entry lists (e.g. previous report vs now, or previous tree vs current tree).
---@return table @{ added = unsupported entries that are new, fixed = previously unsupported entries now supported or gone }
function modCoverage.Diff(oldEntries, newEntries)
	local oldByKey, newByKey = { }, { }
	for _, e in ipairs(oldEntries) do oldByKey[entryKey(e)] = e end
	for _, e in ipairs(newEntries) do newByKey[entryKey(e)] = e end
	local diff = { added = { }, fixed = { }, removed = { } }
	for key, e in pairs(newByKey) do
		local old = oldByKey[key]
		if e.status == "unsupported" and (not old or old.status ~= "unsupported") then
			t_insert(diff.added, e)
		end
	end
	for key, e in pairs(oldByKey) do
		local new = newByKey[key]
		if e.status == "unsupported" then
			if new and new.status == "supported" then
				t_insert(diff.fixed, e)
			elseif not new then
				t_insert(diff.removed, e)
			end
		end
	end
	sortEntries(diff.added)
	sortEntries(diff.fixed)
	sortEntries(diff.removed)
	return diff
end

---Compare lines of two passive trees, ignoring which node they are on. Returns entries of the new
---tree whose text did not exist in the old tree, split into supported and unsupported.
function modCoverage.DiffTrees(oldTree, newTree)
	local oldLines = { }
	for _, e in ipairs(modCoverage.ScanTree(oldTree)) do
		oldLines[e.line] = true
	end
	local result = { newSupported = { }, newUnsupported = { } }
	for _, e in ipairs(modCoverage.ScanTree(newTree)) do
		if not oldLines[e.line] then
			t_insert(e.status == "supported" and result.newSupported or result.newUnsupported, e)
		end
	end
	return result
end

-- Report output

local impactOrder = { "offence", "defence", "utility", "cosmetic" }
local impactLabel = { offence = "Offence", defence = "Defence", utility = "Utility", cosmetic = "Cosmetic" }

local function unsupportedOf(entries)
	local list = { }
	for _, e in ipairs(entries) do
		if e.status == "unsupported" then
			t_insert(list, e)
		end
	end
	return list
end

---Strip fields not needed in JSON and keep only unsupported lines plus totals.
function modCoverage.ToJSONTable(report)
	local function strip(list)
		local out = { }
		for _, e in ipairs(list or { }) do
			t_insert(out, { kind = e.kind, source = e.source, detail = e.detail, nodeId = e.nodeId, line = e.line, status = e.status, statIds = e.statIds, impact = e.impact })
		end
		return out
	end
	local json = { version = report.version, treeVersion = report.treeVersion, generated = report.generated, summary = report.summary, unsupported = strip(unsupportedOf(report.entries)) }
	if report.diff then
		json.diff = { added = strip(report.diff.added), fixed = strip(report.diff.fixed), removed = strip(report.diff.removed) }
	end
	if report.treeDiff then
		json.treeDiff = { previousTreeVersion = report.treeDiff.previousTreeVersion, newSupported = #report.treeDiff.newSupported, newUnsupported = strip(report.treeDiff.newUnsupported) }
	end
	return json
end

local function mdEscape(str)
	return (tostring(str):gsub("|", "\\|"):gsub("\n", " "))
end

local function writeTable(lines, list, withDetail)
	t_insert(lines, withDetail and "| Source | Where | Line | Impact | Game stat id |" or "| Source | Line | Impact | Game stat id |")
	t_insert(lines, withDetail and "|---|---|---|---|---|" or "|---|---|---|---|")
	for _, e in ipairs(list) do
		local stat = e.statIds and ("`" .. table.concat(e.statIds, "`, `") .. "`") or "—"
		if withDetail then
			t_insert(lines, string.format("| %s | %s | %s | %s | %s |", mdEscape(e.source), mdEscape(e.detail or ""), mdEscape(e.line), impactLabel[e.impact] or "", stat))
		else
			t_insert(lines, string.format("| %s | %s | %s | %s |", mdEscape(e.source), mdEscape(e.line), impactLabel[e.impact] or "", stat))
		end
	end
	t_insert(lines, "")
end

---Markdown report for people.
function modCoverage.ToMarkdown(report)
	local lines = { }
	local function add(str) t_insert(lines, str or "") end
	add("# " .. (report.title or "Modifier coverage report"))
	add()
	add(string.format("Path of Building %s · passive tree %s · generated %s", report.version or "?", report.treeVersion or "?", report.generated or "?"))
	add()
	add("A line is **unsupported** when Path of Building cannot parse it, so it is not part of any calculation. ")
	add("**Impact** is an estimate: *Offence* / *Defence* lines may change your numbers, *Utility* / *Cosmetic* lines usually do not. ")
	add("**Game stat id** is the official identifier of the effect (empty if the text could not be matched).")
	add()
	add("## Summary")
	add()
	add("| Scope | Lines | Unsupported | With game stat id | Offence | Defence | Utility | Cosmetic | Sources with a gap |")
	add("|---|---|---|---|---|---|---|---|---|")
	local kindLabel = { unique = "Unique items", node = "Passive nodes", item = "Equipped items" }
	for _, kind in ipairs({ "item", "unique", "node" }) do
		local s = report.summary[kind]
		if s then
			add(string.format("| %s | %d | %d (%.1f%%) | %d | %d | %d | %d | %d | %d of %d |", kindLabel[kind], s.lines, s.unsupported, s.lines > 0 and s.unsupported / s.lines * 100 or 0,
				s.mapped, s.impact.offence or 0, s.impact.defence or 0, s.impact.utility or 0, s.impact.cosmetic or 0, s.sourcesWithGap, s.sources))
		end
	end
	add()
	if report.diff then
		add("## Changes since the previous report")
		add()
		add(string.format("- Newly unsupported: **%d**", #report.diff.added))
		add(string.format("- Now supported: **%d**", #report.diff.fixed))
		add(string.format("- Unsupported lines that disappeared from the data: **%d**", #report.diff.removed))
		add()
		if #report.diff.added > 0 then
			add("### Newly unsupported")
			add()
			writeTable(lines, report.diff.added, true)
		end
		if #report.diff.fixed > 0 then
			add("### Now supported")
			add()
			writeTable(lines, report.diff.fixed, true)
		end
	end
	if report.treeDiff then
		add(string.format("## Passive tree %s compared with %s", report.treeVersion, report.treeDiff.previousTreeVersion))
		add()
		add(string.format("New line texts in this tree: %d supported, **%d unsupported**.", #report.treeDiff.newSupported, #report.treeDiff.newUnsupported))
		add()
		if #report.treeDiff.newUnsupported > 0 then
			writeTable(lines, report.treeDiff.newUnsupported, true)
		end
	end
	local unsupported = unsupportedOf(report.entries)
	for _, impact in ipairs(impactOrder) do
		local list = { }
		for _, e in ipairs(unsupported) do
			if e.impact == impact then
				t_insert(list, e)
			end
		end
		if #list > 0 then
			add(string.format("## Unsupported · %s (%d)", impactLabel[impact], #list))
			add()
			writeTable(lines, list, true)
		end
	end
	return table.concat(lines, "\n")
end

---Build a report table from entries.
---@param opts table? @{ title, previous = <decoded JSON of an earlier report>, previousTree = <PassiveTree>, tree = <PassiveTree> }
function modCoverage.BuildReport(entries, opts)
	opts = opts or { }
	local report = {
		title = opts.title,
		version = launch and launch.versionNumber,
		treeVersion = opts.tree and opts.tree.treeVersion or latestTreeVersion,
		generated = os.date("%Y-%m-%d %H:%M"),
		entries = entries,
		summary = modCoverage.Summarize(entries),
	}
	if opts.previous and opts.previous.unsupported then
		report.diff = modCoverage.Diff(opts.previous.unsupported, entries)
	end
	if opts.previousTree and opts.tree then
		report.treeDiff = modCoverage.DiffTrees(opts.previousTree, opts.tree)
		report.treeDiff.previousTreeVersion = opts.previousTree.treeVersion
	end
	return report
end
