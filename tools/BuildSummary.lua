-- Path of Building
--
-- Build summary (headless): loads build XML files and writes a structured JSON summary per build
-- (character, skills with per-group DPS, equipped items with tags, passives, key stats, config
-- assumptions, modifier coverage). Used by tools/library.py and for AI analysis.
--
--   python tools/runlua.py tools/BuildSummary.lua <build.xml> [out.json]
--   python tools/runlua.py tools/BuildSummary.lua --out-dir <dir> <a.xml> <b.xml> ...
--
-- In --out-dir mode PoB is loaded once; each <name>.xml produces <dir>/<name>.json. A build that
-- fails to load produces { "error": "..." } instead of stopping the batch.

local files, outDir, singleOut = { }, nil, nil
if SCRIPT_ARGS[1] == "--out-dir" then
	outDir = SCRIPT_ARGS[2]
	for i = 3, #SCRIPT_ARGS do table.insert(files, SCRIPT_ARGS[i]) end
else
	files[1], singleOut = SCRIPT_ARGS[1], SCRIPT_ARGS[2]
end
assert(files[1], "usage: BuildSummary.lua <build.xml> [out.json] | --out-dir <dir> <a.xml> ...")

dofile("HeadlessWrapper.lua")
local dkjson = require("dkjson")

local function round(v, n)
	if type(v) ~= "number" then return v end
	local m = 10 ^ (n or 1)
	return math.floor(v * m + 0.5) / m
end

local function readFile(path)
	local f = assert(io.open(path, "rb"))
	local text = f:read("*a")
	f:close()
	return text
end

local function writeFile(path, text)
	local f = assert(io.open(path, "wb"))
	f:write(text)
	f:close()
end

local statKeys = { "TotalDPS", "CombinedDPS", "FullDPS", "TotalDotDPS", "Speed", "HitChance", "CritChance", "CritMultiplier",
	"Life", "LifeUnreserved", "LifeRegenRecovery", "EnergyShield", "Mana", "ManaUnreserved", "Ward", "Armour", "Evasion",
	"PhysicalDamageReduction", "EffectiveBlockChance", "EffectiveSpellBlockChance", "EffectiveSpellSuppressionChance",
	"FireResist", "ColdResist", "LightningResist", "ChaosResist", "FireResistOverCap", "ColdResistOverCap", "LightningResistOverCap",
	"TotalEHP", "PhysicalMaximumHitTaken", "FireMaximumHitTaken", "ColdMaximumHitTaken", "LightningMaximumHitTaken", "ChaosMaximumHitTaken",
	"MovementSpeedMod", "Str", "Dex", "Int", "PowerChargesMax", "FrenzyChargesMax", "EnduranceChargesMax" }

local function groupDPS(calculated)
	if not calculated then return 0 end
	return math.max(calculated.CombinedDPS or 0, calculated.TotalDPS or 0, calculated.MinionCombinedDPS or 0, calculated.MinionTotalDPS or 0)
end

local function summarize(xmlText, buildName)
	loadBuildFromXML(xmlText, buildName)
	local summary = { name = buildName, pobVersion = launch.versionNumber }
	summary.character = {
		class = build.spec.curClassName,
		ascendancy = build.spec.curAscendClassName,
		secondaryAscendancy = build.spec.curSecondaryAscendClassName,
		level = build.characterLevel,
		treeVersion = build.spec.treeVersion,
		bandit = build.bandit,
		pantheon = { major = build.pantheonMajorGod, minor = build.pantheonMinorGod },
	}

	local out = build.calcsTab.mainOutput
	summary.stats = { }
	for _, key in ipairs(statKeys) do
		if out[key] ~= nil then summary.stats[key] = round(out[key], 2) end
	end

	-- Skills: every socket group, its gems, and the DPS PoB calculates when it is the main skill
	summary.skills = { }
	local mainGroup = build.mainSocketGroup
	local best, bestDPS = nil, 0
	for index, group in ipairs(build.skillsTab.socketGroupList) do
		local entry = { index = index, label = group.label, slot = group.slot, enabled = group.enabled, includeInFullDPS = group.includeInFullDPS, main = index == mainGroup, gems = { } }
		for _, gem in ipairs(group.gemList) do
			local name = gem.grantedEffect and gem.grantedEffect.name or gem.nameSpec
			table.insert(entry.gems, { name = name, level = gem.level, quality = gem.quality, enabled = gem.enabled, support = gem.grantedEffect and gem.grantedEffect.support or false })
		end
		if group.enabled and group.displaySkillList and group.displaySkillList[1] then
			build.mainSocketGroup = index
			build.buildFlag = true
			runCallback("OnFrame")
			local o = build.calcsTab.mainOutput
			local env = build.calcsTab.mainEnv
			entry.activeSkill = env.player.mainSkill and env.player.mainSkill.activeEffect.grantedEffect.name
			entry.calculated = { TotalDPS = round(o.TotalDPS, 1), CombinedDPS = round(o.CombinedDPS, 1), TotalDotDPS = round(o.TotalDotDPS, 1) }
			if o.Minion then
				entry.calculated.MinionTotalDPS = round(o.Minion.TotalDPS, 1)
				entry.calculated.MinionCombinedDPS = round(o.Minion.CombinedDPS, 1)
			end
			if groupDPS(entry.calculated) > bestDPS then
				best, bestDPS = entry, groupDPS(entry.calculated)
			end
		end
		table.insert(summary.skills, entry)
	end
	build.mainSocketGroup = mainGroup
	build.buildFlag = true
	runCallback("OnFrame")
	-- The highest-damage skill PoB can calculate; the saved main skill is not always the real one
	summary.primarySkill = best and { group = best.index, name = best.activeSkill, dps = round(bestDPS, 1), minion = best.calculated.MinionCombinedDPS ~= nil } or nil

	-- Equipped items
	summary.items = { }
	local itemsTab = build.itemsTab
	for _, slot in ipairs(itemsTab.orderedSlots or { }) do
		local item = slot.selItemId and itemsTab.items[slot.selItemId]
		if item and slot:IsShown() ~= false then
			local lines = { }
			for _, group in ipairs({ "enchantModLines", "implicitModLines", "explicitModLines", "crucibleModLines" }) do
				for _, ml in ipairs(item[group] or { }) do
					if item:CheckModLineVariant(ml) then
						table.insert(lines, { text = ml.line, kind = (group:gsub("ModLines", "")), supported = ml.modList ~= nil and ml.modList[1] ~= nil and not ml.extra })
					end
				end
			end
			local tagIds = { }
			for id in pairs(autoTags.GetItemTags(item)) do table.insert(tagIds, id) end
			table.sort(tagIds)
			table.insert(summary.items, { slot = slot.slotName, name = item.name, title = item.title, rarity = item.rarity, base = item.baseName, tags = tagIds, mods = lines })
		end
	end

	-- Passives
	summary.passives = { keystones = { }, notables = { }, ascendancy = { }, masteries = { }, count = 0 }
	local nodeTagCount = { }
	for _, node in pairs(build.spec.allocNodes) do
		summary.passives.count = summary.passives.count + 1
		if node.ascendancyName then
			if node.type ~= "AscendClassStart" then table.insert(summary.passives.ascendancy, node.dn) end
		elseif node.type == "Keystone" then
			table.insert(summary.passives.keystones, node.dn)
		elseif node.type == "Notable" then
			table.insert(summary.passives.notables, node.dn)
		elseif node.type == "Mastery" then
			table.insert(summary.passives.masteries, node.dn .. ": " .. table.concat(node.sd or { }, " / "))
		end
		if node.type ~= "ClassStart" and node.type ~= "AscendClassStart" then
			for id in pairs(autoTags.GetNodeTags(node)) do nodeTagCount[id] = (nodeTagCount[id] or 0) + 1 end
		end
	end
	for _, list in pairs({ summary.passives.keystones, summary.passives.notables, summary.passives.ascendancy, summary.passives.masteries }) do
		table.sort(list)
	end
	summary.passives.tagCounts = nodeTagCount

	-- Config assumptions: options the user changed, plus conditions the calculation looked at
	summary.config = { set = { }, conditionsUsed = { }, enemyConditionsUsed = { } }
	for var, value in pairs(build.configTab.input) do
		summary.config.set[var] = value
	end
	local env = build.calcsTab.mainEnv
	for cond in pairs(env.conditionsUsed or { }) do table.insert(summary.config.conditionsUsed, cond) end
	for cond in pairs(env.enemyConditionsUsed or { }) do table.insert(summary.config.enemyConditionsUsed, cond) end
	table.sort(summary.config.conditionsUsed)
	table.sort(summary.config.enemyConditionsUsed)

	-- Tag definitions, so consumers can group tags by category
	summary.tagInfo = { }
	for _, def in ipairs(autoTags.GetTagList()) do
		summary.tagInfo[def.id] = { label = def.label, category = def.category, parent = def.parent }
	end

	-- Coverage of what the build uses
	local report = modCoverage.BuildReport(modCoverage.ScanBuild(build), { tree = build.spec.tree })
	summary.coverage = modCoverage.ToJSONTable(report)
	return summary
end

for _, path in ipairs(files) do
	local buildName = path:match("([^/\\]+)%.xml$") or "build"
	local ok, result = pcall(summarize, readFile(path), buildName)
	local summary = ok and result or { name = buildName, error = tostring(result) }
	local json = dkjson.encode(summary, { indent = true })
	if outDir then
		writeFile(outDir .. "/" .. buildName .. ".json", json)
		print((ok and "ok    " or "error ") .. buildName .. (ok and "" or (": " .. tostring(result))))
	elseif singleOut then
		writeFile(singleOut, json)
		print("written: " .. singleOut)
	else
		print(json)
	end
end
