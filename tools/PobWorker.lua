-- Path of Building
--
-- Persistent headless worker. Loads Path of Building once, then answers JSON requests, one per
-- line on stdin. Each answer is one stdout line starting with "@@RESP " (other stdout lines are
-- PoB's own console output and should be ignored). "@@READY" is printed once loading is done.
--
--   request:  {"id": 1, "method": "summary", "params": {...}}
--   answer:   @@RESP {"id": 1, "ok": true, "result": {...}}  |  {"id": 1, "ok": false, "error": "..."}
--
-- Methods: ping, summary, metrics, simulate, find_uniques, find_passives, list_tags.
-- Builds are passed as XML text ("xml") with a display "name"; the worker reloads only when the
-- XML changed or a simulation modified the loaded build.
--
--   python tools/runlua.py tools/PobWorker.lua

dofile("HeadlessWrapper.lua")
local dkjson = require("dkjson")
local S = dofile(SCRIPT_DIR .. "/lib/summary.lua")
local I = dofile(SCRIPT_DIR .. "/lib/inference.lua")
local Merc = dofile(SCRIPT_DIR .. "/lib/mercenary.lua")
local round = S.round

local loadedXml, dirty = nil, true
-- Blended minion DPS for a buff with partial uptime (set by applyInference, read by metrics)
local blend = nil
-- Config values as saved in the build, so inference never overrides what the user set
local userConfig = { }

local mercenaryApplied = nil

local function loadFresh(params)
	-- The mercenary's buffs are calculated in a throw-away build first (cached), then put into the player's Party tab
	local mercSpec, mercReport, mercExport
	if params.mercenary then
		mercSpec, mercReport = Merc.resolve(params.mercenary)
		mercExport = Merc.export(mercSpec)
	end
	loadBuildFromXML(params.xml, params.name or "build")
	userConfig = copyTable(build.configTab.input)
	blend = nil
	mercenaryApplied = mercExport and Merc.apply(mercSpec, mercExport, mercReport) or nil
end

local function ensureBuild(params)
	assert(params.xml, "missing build xml")
	if dirty or loadedXml ~= params.xml then
		loadFresh(params)
		loadedXml, dirty = params.xml, false
	end
end

local function recalc()
	build.buildFlag = true
	runCallback("OnFrame")
	return build.calcsTab.mainOutput
end

-- Estimate and apply Config values the build leaves at 0 (e.g. withered stacks). Values the user
-- saved in the build, or set through a config_set change in this request, are never overridden.
local function applyInference(p)
	if p.infer == false then
		return nil
	end
	local explicit = { }
	for _, change in ipairs(p.changes or { }) do
		if change.type == "config_set" then explicit[change.key] = true end
	end
	blend = nil
	local list = I.infer(build, { minionCount = p.minionCount, summonRate = p.summonRate })
	local changed = false
	for _, inf in ipairs(list) do
		local saved = userConfig[inf.key]
		if explicit[inf.key] then
			inf.applied, inf.skipped = false, "set explicitly in this request or the saved settings"
		elseif inf.needs then
			inf.applied, inf.skipped = false, "needs " .. inf.needs .. " from play"
		elseif saved ~= nil and saved ~= 0 and not inf.override then
			inf.applied, inf.skipped = false, "the build already sets " .. inf.key .. " = " .. tostring(saved)
		elseif inf.value == false then
			inf.applied, inf.skipped = false, "estimate too low to switch on"
		else
			build.configTab.input[inf.key] = inf.value
			inf.applied = true
			changed = true
		end
	end
	if changed then
		build.configTab:BuildModList()
		recalc()
	end
	-- Partial uptime of an on/off buff: PoB only knows on or off, so measure both and blend the minion DPS
	for _, inf in ipairs(list) do
		if inf.applied and inf.blend and inf.uptime and inf.uptime < 1 then
			local on = build.calcsTab.mainOutput.Minion and build.calcsTab.mainOutput.Minion.CombinedDPS or 0
			build.configTab.input[inf.key] = false
			build.configTab:BuildModList()
			local o = recalc()
			local off = o.Minion and o.Minion.CombinedDPS or 0
			build.configTab.input[inf.key] = inf.value
			build.configTab:BuildModList()
			recalc()
			blend = { key = inf.key, uptime = inf.uptime, on = on, off = off, value = off + inf.uptime * (on - off) }
			inf.minionDPSWithBuff, inf.minionDPSWithoutBuff, inf.minionDPSBlended = round(on, 1), round(off, 1), round(blend.value, 1)
		end
	end
	return list
end

local function findGroup(ref)
	local groups = build.skillsTab.socketGroupList
	if type(ref) == "number" then
		return assert(groups[ref], "no socket group " .. ref), ref
	end
	ref = tostring(ref):lower()
	for index, group in ipairs(groups) do
		for _, gem in ipairs(group.gemList) do
			if (gem.nameSpec or ""):lower() == ref then
				return group, index
			end
		end
	end
	error("no socket group contains gem '" .. tostring(ref) .. "'")
end

-- Pick the group with the highest damage PoB can calculate
local function primaryGroup()
	local best, bestDPS = build.mainSocketGroup, -1
	for index, group in ipairs(build.skillsTab.socketGroupList) do
		if group.enabled and group.displaySkillList and group.displaySkillList[1] then
			build.mainSocketGroup = index
			local o = recalc()
			local dps = math.max(o.CombinedDPS or 0, o.Minion and o.Minion.CombinedDPS or 0)
			if dps > bestDPS then
				best, bestDPS = index, dps
			end
		end
	end
	build.mainSocketGroup = best
	recalc()
	return best
end

-- Minion skills of the main skill (e.g. a Phantasm's melee attack and its spell projectiles)
local function minionSkillList()
	local skill = build.calcsTab.mainEnv.player.mainSkill
	local list = { }
	if skill and skill.minion then
		for _, minionSkill in ipairs(skill.minion.activeSkillList) do
			table.insert(list, minionSkill.activeEffect.grantedEffect.name)
		end
	end
	return list, skill
end

local function selectMinionSkill(ref)
	local list, skill = minionSkillList()
	assert(#list > 0, "the main skill has no minion skills")
	local index = tonumber(ref)
	if not index then
		local want = tostring(ref):lower()
		for i, name in ipairs(list) do
			if name:lower() == want or name:lower():find(want, 1, true) then
				index = i
				break
			end
		end
	end
	assert(index and list[index], "no minion skill '" .. tostring(ref) .. "' (available: " .. table.concat(list, ", ") .. ")")
	skill.activeEffect.srcInstance.skillMinionSkill = index
	skill.activeEffect.srcInstance.skillMinionSkillCalcs = index
	recalc()
	return list[index]
end

local function metrics()
	local o = build.calcsTab.mainOutput
	local env = build.calcsTab.mainEnv
	local skill = env.player.mainSkill
	local m = {
		mainGroup = build.mainSocketGroup,
		mainSkill = skill and skill.activeEffect.grantedEffect.name,
		playerDPS = round(o.CombinedDPS or 0, 1),
		minionDPS = o.Minion and round(o.Minion.CombinedDPS or 0, 1) or nil,
		mercenary = mercenaryApplied,
		mercenaryDamageTakenPercent = (o.MercenaryAllyDamageMitigation or 0) > 0 and o.MercenaryAllyDamageMitigation or nil,
	}
	-- Only while the blended buff is still on (a later change could have switched it off)
	if blend and blend.on > 0 and o.Minion and build.configTab.input[blend.key] then
		m.minionDPSFullBuff = m.minionDPS
		m.minionDPS = round(blend.value * (o.Minion.CombinedDPS or 0) / blend.on, 1)
		m.blendedBy = string.format("%s uptime %.0f%%", blend.key, blend.uptime * 100)
	end
	local list = minionSkillList()
	if #list > 0 then
		local minionMain = env.minion and env.minion.mainSkill
		m.minionSkill = minionMain and minionMain.activeEffect.grantedEffect.name
		m.minionSkills = list
	end
	for _, key in ipairs({ "Life", "EnergyShield", "Mana", "ManaUnreserved", "LifeUnreserved", "Ward", "Armour", "Evasion", "TotalEHP",
		"PhysicalMaximumHitTaken", "FireMaximumHitTaken", "ColdMaximumHitTaken", "LightningMaximumHitTaken", "ChaosMaximumHitTaken",
		"FireResist", "ColdResist", "LightningResist", "ChaosResist", "EffectiveBlockChance", "EffectiveSpellBlockChance",
		"EffectiveSpellSuppressionChance", "MovementSpeedMod", "Str", "Dex", "Int", "LifeRegenRecovery", "Speed", "HitChance", "CritChance" }) do
		if type(o[key]) == "number" then
			m[key] = round(o[key], 2)
		end
	end
	return m
end

local function findNode(ref)
	if type(ref) == "number" or tostring(ref):match("^%d+$") then
		return assert(build.spec.nodes[tonumber(ref)], "no passive node " .. tostring(ref))
	end
	local want, fallback = tostring(ref):lower(), nil
	for _, node in pairs(build.spec.nodes) do
		if node.dn and node.dn:lower() == want then
			if node.ascendancyName == nil or node.ascendancyName == build.spec.curAscendClassName then
				return node
			end
			fallback = fallback or node
		end
	end
	return assert(fallback, "no passive node named '" .. tostring(ref) .. "'")
end

local function findUnique(name)
	local want = name:lower()
	for _, item in pairs(main.uniqueDB.list) do
		if (item.title or ""):lower() == want or (item.name or ""):lower() == want then
			return item
		end
	end
	error("no unique named '" .. name .. "'")
end

local function setGem(gem, name, level, quality)
	local errMsg, gemData = build.skillsTab:FindSkillGem(name)
	assert(gemData, errMsg or ("unknown gem '" .. name .. "'"))
	gem.nameSpec, gem.gemId, gem.skillId, gem.gemData, gem.grantedEffect = gemData.name, nil, nil, nil, nil
	gem.level = level or gem.level or gemData.naturalMaxLevel or 20
	gem.quality = quality or gem.quality or 0
	gem.enabled = true
	return gemData.name
end

-- Each change returns a short description of what was done
local changeHandlers = {
	main_group = function(c)
		local _, index = findGroup(c.group)
		build.mainSocketGroup = index
		return "main skill group " .. index
	end,
	minion_skill = function(c)
		return "minion skill: " .. selectMinionSkill(c.skill)
	end,
	gem_replace = function(c)
		local group, index = findGroup(c.group or c.gem)
		for _, gem in ipairs(group.gemList) do
			if (gem.nameSpec or ""):lower() == c.gem:lower() then
				local new = setGem(gem, c.with, c.level, c.quality)
				build.skillsTab:ProcessSocketGroup(group)
				return string.format("group %d: %s -> %s", index, c.gem, new)
			end
		end
		error("gem '" .. c.gem .. "' not found in group " .. index)
	end,
	group_add = function(c)
		local group = { label = c.label or "", enabled = true, includeInFullDPS = false, slot = c.slot, gemList = { } }
		local names = { }
		for _, name in ipairs(assert(c.gems, "group_add needs gems")) do
			local gem = { enableGlobal1 = true, enableGlobal2 = true, count = 1 }
			table.insert(names, setGem(gem, name, c.level, c.quality))
			table.insert(group.gemList, gem)
		end
		table.insert(build.skillsTab.socketGroupList, group)
		build.skillsTab:ProcessSocketGroup(group)
		return "new group: " .. table.concat(names, ", ")
	end,
	gem_add = function(c)
		local group, index = findGroup(c.group)
		local gem = { enableGlobal1 = true, enableGlobal2 = true, count = 1 }
		local new = setGem(gem, c.gem, c.level, c.quality)
		table.insert(group.gemList, gem)
		build.skillsTab:ProcessSocketGroup(group)
		return string.format("group %d: added %s", index, new)
	end,
	gem_remove = function(c)
		local group, index = findGroup(c.group or c.gem)
		for i, gem in ipairs(group.gemList) do
			if (gem.nameSpec or ""):lower() == c.gem:lower() then
				table.remove(group.gemList, i)
				build.skillsTab:ProcessSocketGroup(group)
				return string.format("group %d: removed %s", index, c.gem)
			end
		end
		error("gem '" .. c.gem .. "' not found in group " .. index)
	end,
	gem_level = function(c)
		local group, index = findGroup(c.group or c.gem)
		for _, gem in ipairs(group.gemList) do
			if (gem.nameSpec or ""):lower() == c.gem:lower() then
				gem.level = c.level or gem.level
				gem.quality = c.quality or gem.quality
				build.skillsTab:ProcessSocketGroup(group)
				return string.format("group %d: %s level %s quality %s", index, c.gem, tostring(gem.level), tostring(gem.quality))
			end
		end
		error("gem '" .. c.gem .. "' not found in group " .. index)
	end,
	item_equip = function(c)
		local slot = assert(build.itemsTab.slots[c.slot], "no item slot '" .. tostring(c.slot) .. "'")
		local raw = c.raw or findUnique(assert(c.unique, "item_equip needs 'unique' or 'raw'")).raw
		local item = new("Item"):Item(raw)
		item:NormaliseQuality()
		build.itemsTab:AddItem(item, true)
		slot:SetSelItemId(item.id)
		build.itemsTab:PopulateSlots()
		return string.format("%s: equipped %s", c.slot, item.name)
	end,
	item_remove = function(c)
		local slot = assert(build.itemsTab.slots[c.slot], "no item slot '" .. tostring(c.slot) .. "'")
		slot:SetSelItemId(0)
		build.itemsTab:PopulateSlots()
		return string.format("%s: emptied", c.slot)
	end,
	passive_add = function(c)
		local node = findNode(c.node)
		if node.alloc then return node.dn .. " already allocated" end
		assert(node.path, node.dn .. " cannot be reached from the current tree")
		local cost = #node.path
		build.spec:AllocNode(node)
		build.spec:AddUndoState()
		return string.format("allocated %s (%d point%s)", node.dn, cost, cost == 1 and "" or "s")
	end,
	passive_remove = function(c)
		local node = findNode(c.node)
		if not node.alloc then return node.dn .. " was not allocated" end
		local freed = #(node.depends or { node })
		build.spec:DeallocNode(node)
		build.spec:AddUndoState()
		return string.format("removed %s (%d point%s freed)", node.dn, freed, freed == 1 and "" or "s")
	end,
	config_set = function(c)
		build.configTab.input[c.key] = c.value
		build.configTab:BuildModList()
		return string.format("config %s = %s", c.key, tostring(c.value))
	end,
}

local methods = { }

function methods.ping()
	return { pong = true, pobVersion = launch.versionNumber, treeVersion = latestTreeVersion }
end

function methods.summary(p)
	dirty = true
	return S.summarize(assert(p.xml, "missing build xml"), p.name or "build")
end

local function selectMain(p)
	if p.group then
		local _, index = findGroup(p.group)
		build.mainSocketGroup = index
		recalc()
	else
		primaryGroup()
	end
	if p.minionSkill then
		selectMinionSkill(p.minionSkill)
	end
end

function methods.metrics(p)
	dirty = true
	ensureBuild(p)
	selectMain(p)
	local inferred = applyInference(p)
	local m = metrics()
	m.inferred = inferred
	return m
end

function methods.simulate(p)
	dirty = true
	ensureBuild(p)
	selectMain(p)
	local inferredBefore = applyInference({ infer = p.infer, minionCount = p.minionCount, summonRate = p.summonRate, changes = { } })
	local before = metrics()
	local applied = { }
	for i, change in ipairs(p.changes or { }) do
		local handler = changeHandlers[change.type]
		if not handler then
			error(string.format("change %d: unknown type '%s'", i, tostring(change.type)), 0)
		end
		local ok, result = pcall(handler, change)
		if not ok then
			error(string.format("change %d (%s): %s", i, change.type, (tostring(result):gsub("^.-:%d+: ", ""))), 0)
		end
		table.insert(applied, result)
	end
	recalc()
	-- Re-estimate after the changes (they may add or remove sources such as Unholy Might)
	local inferredAfter = applyInference(p)
	local after = metrics()
	local diff = { }
	for key, value in pairs(after) do
		if type(value) == "number" and type(before[key]) == "number" and value ~= before[key] then
			diff[key] = { before = before[key], after = value, change = round(value - before[key], 2),
				percent = before[key] ~= 0 and round((value / before[key] - 1) * 100, 1) or nil }
		end
	end
	dirty = true
	return { applied = applied, before = before, after = after, changed = diff, inferredBefore = inferredBefore, inferredAfter = inferredAfter }
end

-- Leave-one-out analysis: remove each part (item, support gem, notable/keystone) on its own and
-- measure what the build loses. Parts whose removal changes nothing PoB can measure but that
-- carry mechanics PoB does not model (minion count, triggers, unsupported lines) are reported as
-- "functional" rather than useless.
local functionalTags = { minion = true, phantasm = true, zombie = true, skeleton = true, spectre = true, golem = true,
	ragingspirit = true, animated = true, holyrelic = true, sentinel = true, spider = true, reaper = true, totem = true, trapmine = true, brand = true }

local function classify(dpsPct, ehpPct, functional)
	if dpsPct <= -10 then return "core damage" end
	if dpsPct <= -2 then return "damage" end
	if ehpPct <= -10 then return "core defence" end
	if ehpPct <= -2 then return "defence" end
	if dpsPct >= 2 then return "hurts damage" end
	if functional then return "functional (not measured by PoB)" end
	return "no measurable effect"
end

function methods.contributions(p)
	dirty = true
	ensureBuild(p)
	selectMain(p)
	-- Fix the main group once; finding the strongest group on every run would be slow
	p.group = p.group or build.mainSocketGroup
	local baseChanges = p.changes or { }
	local function run(extra)
		loadFresh(p)
		selectMain(p)
		for _, change in ipairs(baseChanges) do assert(changeHandlers[change.type], "unknown change type " .. tostring(change.type))(change) end
		local desc = extra and changeHandlers[extra.type](extra)
		recalc()
		applyInference(p)
		local ok, m = pcall(metrics)
		m = ok and m or { }
		local points = 0
		for _ in pairs(build.spec.allocNodes) do points = points + 1 end
		m.allocatedNodes = points
		return m, desc
	end
	local base = run(nil)
	local function dpsOf(m) return math.max(m.playerDPS or 0, m.minionDPS or 0) end
	local baseDPS, baseEHP = dpsOf(base), base.TotalEHP or 0
	local parts = { }
	local function measure(kind, name, detail, change, functional)
		local ok, after = pcall(run, change)
		if not ok then
			table.insert(parts, { kind = kind, name = name, detail = detail, error = (tostring(after):gsub("^.-%.lua:%d+: ", "")) })
			return
		end
		local dps, ehp = dpsOf(after), after.TotalEHP or 0
		local lostSkill = after.mainSkill ~= base.mainSkill
		local dpsPct = baseDPS > 0 and round((dps / baseDPS - 1) * 100, 1) or 0
		local ehpPct = baseEHP > 0 and round((ehp / baseEHP - 1) * 100, 1) or 0
		if lostSkill then dpsPct = -100 end
		local nodesRemoved = kind ~= "item" and kind ~= "support gem" and (base.allocatedNodes - (after.allocatedNodes or 0)) or nil
		local role = lostSkill and "enables main skill" or classify(dpsPct, ehpPct, functional)
		if nodesRemoved and nodesRemoved > 10 then
			-- Removing this node disconnects a large part of the tree; the loss is not the node's own value
			role = "tree hub (" .. role .. " incl. " .. nodesRemoved .. " points)"
		end
		table.insert(parts, { kind = kind, name = name, detail = detail, dpsPct = dpsPct, ehpPct = ehpPct, lostMainSkill = lostSkill or nil,
			nodesRemoved = nodesRemoved,
			role = role, alsoFunctional = functional and not role:match("functional") or nil })
	end
	-- Items (flasks are skipped: their effects depend on Config flask settings)
	loadFresh(p)
	local itemsTab = build.itemsTab
	local itemParts, gemParts, nodeParts = { }, { }, { }
	for _, slot in ipairs(itemsTab.orderedSlots or { }) do
		local item = slot.selItemId and itemsTab.items[slot.selItemId]
		if item and not slot.slotName:match("^Flask") and slot:IsShown() ~= false then
			local tags, functional = autoTags.GetItemTags(item), false
			for id in pairs(tags) do if functionalTags[id] then functional = true end end
			for _, group in ipairs({ "implicitModLines", "explicitModLines" }) do
				for _, ml in ipairs(item[group] or { }) do
					if item:CheckModLineVariant(ml) and (ml.extra or not ml.modList or not ml.modList[1]) then functional = true end
				end
			end
			table.insert(itemParts, { slot.slotName, item.name, functional })
		end
	end
	for index, group in ipairs(build.skillsTab.socketGroupList) do
		if group.enabled then
			for _, gem in ipairs(group.gemList) do
				local effect = gem.gemData and gem.gemData.grantedEffect
				if effect and effect.support and gem.enabled then
					local types = effect.skillTypes or { }
					local functional = types[SkillType.Triggered] or types[SkillType.InbuiltTrigger] or types[SkillType.CreatesMinion] or types[SkillType.Minion]
						or (effect.name or ""):match("^Cast ") ~= nil or (effect.name or ""):match("Summon") ~= nil
					-- Area / projectile-count supports help clearing packs; PoB's DPS is single-target
					for _, word in ipairs({ "Multiple Projectiles", "Pierce", "Fork", "Chain", "Unleash", "Volley", "Barrage" }) do
						if (effect.name or ""):find(word, 1, true) then functional = true end
					end
					table.insert(gemParts, { index, gem.nameSpec, functional })
				end
			end
		end
	end
	if p.includePassives ~= false then
		for _, node in pairs(build.spec.allocNodes) do
			if (node.type == "Notable" or node.type == "Keystone") and not node.ascendancyName then
				local functional = false
				for id in pairs(autoTags.GetNodeTags(node)) do if functionalTags[id] then functional = true end end
				table.insert(nodeParts, { node.id, node.dn, node.type, functional })
			end
		end
	end
	for _, it in ipairs(itemParts) do
		measure("item", it[2], it[1], { type = "item_remove", slot = it[1] }, it[3])
	end
	for _, g in ipairs(gemParts) do
		measure("support gem", g[2], "group " .. g[1], { type = "gem_remove", gem = g[2], group = g[1] }, g[3])
	end
	for _, n in ipairs(nodeParts) do
		measure(n[3]:lower(), n[2], "node " .. n[1], { type = "passive_remove", node = n[1] }, n[4])
	end
	table.sort(parts, function(a, b) return (a.dpsPct or 0) + (a.ehpPct or 0) * 0.001 < (b.dpsPct or 0) + (b.ehpPct or 0) * 0.001 end)
	dirty = true
	loadFresh(p)
	selectMain(p)
	for _, change in ipairs(baseChanges) do changeHandlers[change.type](change) end
	recalc()
	local inferred = applyInference(p)
	return { baseline = base, inferred = inferred, parts = parts, note = "dpsPct/ehpPct = change when that part alone is removed; passives are removed with the points that depend on them" }
end

local function resolveTags(list)
	local ids = { }
	for _, word in ipairs(list or { }) do
		local found, unknown = autoTags.ParseQuery(word)
		assert(#unknown == 0, "unknown tag '" .. tostring(unknown[1]) .. "' (see list_tags)")
		for _, id in ipairs(found) do table.insert(ids, id) end
	end
	return ids
end

function methods.infer(p)
	dirty = true
	ensureBuild(p)
	selectMain(p)
	for _, change in ipairs(p.changes or { }) do changeHandlers[change.type](change) end
	recalc()
	return I.infer(build, { minionCount = p.minionCount })
end

function methods.find_uniques(p)
	local ids = resolveTags(p.tags)
	local slotWant = p.slot and p.slot:lower()
	local results = { }
	for _, item in pairs(main.uniqueDB.list) do
		local tags = autoTags.GetItemTags(item)
		local slot = item:GetPrimarySlot() or ""
		local slotOk = not slotWant or slot:lower():gsub(" %d$", "") == slotWant:gsub(" %d$", "") or (item.type or ""):lower() == slotWant
		if slotOk and autoTags.HasAll(tags, ids) then
			local lines = { }
			for _, group in ipairs({ "implicitModLines", "explicitModLines" }) do
				for _, ml in ipairs(item[group]) do
					if item:CheckModLineVariant(ml) then table.insert(lines, ml.line) end
				end
			end
			table.insert(results, { name = item.title or item.name, base = item.baseName, type = item.type, slot = slot, levelRequirement = item.requirements and item.requirements.level,
				tags = autoTags.Describe(tags), mods = lines })
		end
	end
	table.sort(results, function(a, b) return a.name < b.name end)
	local limit = p.limit or 30
	local total = #results
	while #results > limit do table.remove(results) end
	return { total = total, items = results }
end

function methods.find_passives(p)
	local ids = resolveTags(p.tags)
	local types = { }
	for _, t in ipairs(p.types or { "Notable", "Keystone" }) do types[t:lower()] = true end
	local tree = main:LoadTree(latestTreeVersion)
	local results = { }
	for _, node in pairs(tree.nodes) do
		local kind = node.ascendancyName and "ascendancy" or (node.type or ""):lower()
		if (types[kind] or (types.ascendancy and node.ascendancyName)) and node.dn and autoTags.HasAll(autoTags.GetNodeTags(node), ids) then
			if not p.ascendancy or (node.ascendancyName or ""):lower() == p.ascendancy:lower() then
				table.insert(results, { id = node.id, name = node.dn, type = node.type, ascendancy = node.ascendancyName, stats = node.sd, tags = autoTags.Describe(autoTags.GetNodeTags(node)) })
			end
		end
	end
	table.sort(results, function(a, b) return a.name < b.name end)
	local limit = p.limit or 30
	local total = #results
	while #results > limit do table.remove(results) end
	return { total = total, passives = results }
end

-- Damage formula of the main skill, read from PoB's own calculation breakdown:
-- base damage -> increased -> more -> conversion -> hit -> enemy mitigation -> crit -> speed -> DPS
local function cleanLine(line)
	return (tostring(line):gsub("%^x%x%x%x%x%x%x", ""):gsub("%^%d", ""):gsub("%s+$", ""))
end

local function textLines(list)
	local out = { }
	for _, line in ipairs(list or { }) do
		if type(line) == "string" then
			table.insert(out, cleanLine(line))
		end
	end
	return out
end

local function multiplier(text)
	return text and tonumber(tostring(text):match("x%s*([%d%.]+)")) or nil
end

function methods.damage_breakdown(p)
	dirty = true
	ensureBuild(p)
	selectMain(p)
	for _, change in ipairs(p.changes or { }) do changeHandlers[change.type](change) end
	recalc()
	local inferred = applyInference(p)
	local env = build.calcsTab.mainEnv
	local actor = env.minion or env.player
	local out, bd = actor.output, actor.breakdown or { }
	-- Attacks keep their per-weapon numbers under MainHand / OffHand
	local hand
	if out.MainHand and (out.MainHand.TotalDPS or 0) > 0 then
		hand = "MainHand"
	elseif out.OffHand and (out.OffHand.TotalDPS or 0) > 0 then
		hand = "OffHand"
	end
	local handOut = hand and out[hand] or out
	local handBd = hand and bd[hand] or bd
	local result = {
		actor = env.minion and "minion" or "player",
		skill = actor.mainSkill and actor.mainSkill.activeEffect.grantedEffect.name,
		mainSkill = env.player.mainSkill and env.player.mainSkill.activeEffect.grantedEffect.name,
		weapon = hand,
		damageTypes = { },
		speed = { value = round(out.Speed or 0, 3), lines = textLines(handBd.Speed or bd.Speed) },
		hitChance = round(handOut.HitChance or out.HitChance or 0, 1),
		crit = { chance = round(handOut.CritChance or out.CritChance or 0, 2), multiplier = round(handOut.CritMultiplier or out.CritMultiplier or 0, 3),
			effect = round(handOut.CritEffect or out.CritEffect or 1, 4) },
		averageHit = round(handOut.AverageHit or out.AverageHit or 0, 1),
		hitDPS = round(out.TotalDPS or 0, 1),
		dot = { },
		combinedDPS = round(out.CombinedDPS or 0, 1),
		inferred = inferred,
	}
	for _, dtype in ipairs({ "Physical", "Lightning", "Cold", "Fire", "Chaos" }) do
		local hitAvg = handOut[dtype .. "HitAverage"] or 0
		local typeBd = handBd[dtype]
		if typeBd and (hitAvg > 0 or (typeBd.damageTypes and typeBd.damageTypes[1])) then
			local rows = { }
			for _, row in ipairs(typeBd.damageTypes or { }) do
				table.insert(rows, { from = row.source, base = row.base, increased = multiplier(row.inc), more = multiplier(row.more),
					convertedIn = row.convSrc or nil, total = row.total, convertedTo = row.convDst or nil, gainedAs = row.gainDst or nil })
			end
			table.insert(result.damageTypes, {
				type = dtype,
				hitAverage = round(hitAvg, 1),
				portionPercent = 0,
				lines = textLines(typeBd),
				rows = rows,
				enemyMitigation = (function()
					local lines = textLines(handBd[dtype .. "EffMult"])
					local value = handOut[dtype .. "EffMult"]
					if not value and #lines > 0 then
						value = tonumber(lines[#lines]:match("^=%s*([%d%.]+)"))
					end
					return { value = value and round(value, 4), lines = lines }
				end)(),
			})
		end
	end
	local totalHit = 0
	for _, dt in ipairs(result.damageTypes) do totalHit = totalHit + dt.hitAverage end
	for _, dt in ipairs(result.damageTypes) do
		dt.portionPercent = totalHit > 0 and round(dt.hitAverage / totalHit * 100, 1) or 0
	end
	for _, key in ipairs({ "BleedDPS", "PoisonDPS", "IgniteDPS", "BurningGroundDPS", "CausticGroundDPS", "TotalDot", "ImpaleDPS", "DecayDPS" }) do
		if (out[key] or 0) > 0 then
			result.dot[key] = round(out[key], 1)
		end
	end
	return result
end

-- Remove one modifier line at a time from every equipped item (flasks excluded) and measure
function methods.mod_contributions(p)
	dirty = true
	local function setup()
		loadFresh(p)
		selectMain(p)
		for _, change in ipairs(p.changes or { }) do changeHandlers[change.type](change) end
		recalc()
		applyInference(p)
	end
	ensureBuild(p)
	selectMain(p)
	p.group = p.group or build.mainSocketGroup
	setup()
	local function dpsOf(m) return math.max(m.playerDPS or 0, m.minionDPS or 0) end
	local base = metrics()
	local baseDPS, baseEHP = dpsOf(base), base.TotalEHP or 0
	local targets = { }
	for _, slot in ipairs(build.itemsTab.orderedSlots or { }) do
		local item = slot.selItemId and build.itemsTab.items[slot.selItemId]
		if item and not slot.slotName:match("^Flask") and slot:IsShown() ~= false then
			for _, group in ipairs({ "implicitModLines", "explicitModLines" }) do
				for index, ml in ipairs(item[group] or { }) do
					if item:CheckModLineVariant(ml) then
						table.insert(targets, { slot = slot.slotName, item = item.name, group = group, index = index, line = ml.line })
					end
				end
			end
		end
	end
	local parts = { }
	for _, t in ipairs(targets) do
		setup()
		local ok, err = pcall(function()
			local slot = build.itemsTab.slots[t.slot]
			local original = build.itemsTab.items[slot.selItemId]
			local copy = new("Item"):Item(original:BuildRaw())
			table.remove(copy[t.group], t.index)
			copy:BuildAndParseRaw()
			build.itemsTab:AddItem(copy, true)
			slot:SetSelItemId(copy.id)
			build.itemsTab:PopulateSlots()
			recalc()
			applyInference(p)
		end)
		local entry = { slot = t.slot, item = t.item, line = t.line, kind = t.group == "implicitModLines" and "implicit" or "explicit" }
		if ok then
			local m = metrics()
			entry.dpsPct = baseDPS > 0 and round((dpsOf(m) / baseDPS - 1) * 100, 1) or 0
			entry.ehpPct = baseEHP > 0 and round(((m.TotalEHP or 0) / baseEHP - 1) * 100, 1) or 0
		else
			entry.error = (tostring(err):gsub("^.-%.lua:%d+: ", ""))
		end
		table.insert(parts, entry)
	end
	table.sort(parts, function(a, b) return (a.dpsPct or 0) + (a.ehpPct or 0) * 0.001 < (b.dpsPct or 0) + (b.ehpPct or 0) * 0.001 end)
	dirty = true
	return { baseline = base, parts = parts }
end

-- Switch off each Config assumption the build turned on and measure what it was worth
local configSkip = { bandit = true, pantheonMajorGod = true, pantheonMinorGod = true, resistancePenalty = true, enemySizePreset = true,
	presetBossSkills = true, doomBlastSource = true, repeatMode = true, resourceGainMode = true, plagueBearerState = true,
	ChanceToIgnoreEnemyPhysicalDamageReductionMode = true }

function methods.config_sensitivity(p)
	dirty = true
	ensureBuild(p)
	selectMain(p)
	p.group = p.group or build.mainSocketGroup
	local saved = copyTable(userConfig)
	local function dpsOf(m) return math.max(m.playerDPS or 0, m.minionDPS or 0) end
	local function run(change)
		loadFresh(p)
		selectMain(p)
		for _, c in ipairs(p.changes or { }) do changeHandlers[c.type](c) end
		if change then changeHandlers.config_set(change) end
		recalc()
		applyInference(p)
		return metrics()
	end
	local base = run(nil)
	local baseDPS, baseEHP = dpsOf(base), base.TotalEHP or 0
	local parts = { }
	for key, value in pairs(saved) do
		if not configSkip[key] and not key:match("BypassCD$") then
			local off
			if value == true then off = false
			elseif type(value) == "number" and value ~= 0 and (key:match("^multiplier") or key:match("^override") or key:match("Count$") or key:match("Stages$")) then off = 0
			elseif key == "enemyIsBoss" and value ~= "None" then off = "None" end
			if off ~= nil then
				local ok, m = pcall(run, { type = "config_set", key = key, value = off })
				if ok then
					table.insert(parts, { key = key, value = value, testedWith = off,
						dpsPct = baseDPS > 0 and round((dpsOf(m) / baseDPS - 1) * 100, 1) or 0,
						ehpPct = baseEHP > 0 and round(((m.TotalEHP or 0) / baseEHP - 1) * 100, 1) or 0 })
				end
			end
		end
	end
	table.sort(parts, function(a, b) return math.abs(a.dpsPct) + math.abs(a.ehpPct) > math.abs(b.dpsPct) + math.abs(b.ehpPct) end)
	dirty = true
	return { baseline = base, parts = parts, note = "dpsPct/ehpPct = change when that assumption is switched off (enemyIsBoss: set to None)" }
end

-- Passive point budget: level - 1 + 23 quest points + extra points (as the PoB GUI counts them)
local function pointBudget()
	local used = build.spec:CountAllocNodes()
	local extra = build.calcsTab.mainOutput and build.calcsTab.mainOutput.ExtraPoints or 0
	return used, build.characterLevel - 1 + 23 + extra
end

local function extendedMetrics()
	local m = metrics()
	m.passivePointsUsed, m.passivePointsAvailable = pointBudget()
	local o = build.calcsTab.mainOutput
	m.minionLimit = o.ActiveMinionLimit
	m.LifeUnreserved = o.LifeUnreserved and round(o.LifeUnreserved, 1)
	m.ManaUnreserved = o.ManaUnreserved and round(o.ManaUnreserved, 1)
	return m
end

-- Apply changes and evaluate; used by the optimizer for many candidates in one request
function methods.evaluate(p)
	dirty = true
	local results = { }
	for _, candidate in ipairs(p.candidates or { { } }) do
		local ok, res = pcall(function()
			loadFresh(p)
			selectMain(p)
			local applied = { }
			for _, change in ipairs(p.changes or { }) do changeHandlers[change.type](change) end
			for _, change in ipairs(candidate) do table.insert(applied, changeHandlers[change.type](change)) end
			recalc()
			local inferred = applyInference(p)
			local m = extendedMetrics()
			m.inferred = inferred
			return { applied = applied, metrics = m }
		end)
		table.insert(results, ok and res or { error = (tostring(res):gsub("^.-%.lua:%d+: ", "")) })
	end
	return results
end

-- What the optimizer may try for this build
local defensiveSkills = { "Determination", "Grace", "Discipline", "Purity of Elements", "Vitality", "Defiance Banner", "Molten Shell",
	"Steelskin", "Arctic Armour", "Petrified Blood", "Tempest Shield", "Flesh and Stone" }
local minionBuffSkills = { "Zealotry", "Dread Banner", "Haste", "Pride", "Malevolence", "Wrath", "Anger", "Hatred", "Flesh Offering", "Convocation" }

function methods.candidates(p)
	dirty = true
	ensureBuild(p)
	selectMain(p)
	local result = { supports = { }, skills = { }, passives = { }, uniques = { } }
	local mainSkill = build.calcsTab.mainEnv.player.mainSkill
	for _, gem in pairs(data.gems) do
		local effect = gem.grantedEffect
		if effect and effect.support and not gem.name:match("^Vaal") and calcLib.canGrantedEffectSupportActiveSkill(effect, mainSkill) then
			table.insert(result.supports, gem.name)
		end
	end
	table.sort(result.supports)
	local present = { }
	for _, group in ipairs(build.skillsTab.socketGroupList) do
		for _, gem in ipairs(group.gemList) do present[(gem.nameSpec or ""):lower()] = true end
	end
	for _, name in ipairs(defensiveSkills) do if not present[name:lower()] then table.insert(result.skills, { name = name, purpose = "defence" }) end end
	for _, name in ipairs(minionBuffSkills) do if not present[name:lower()] then table.insert(result.skills, { name = name, purpose = "damage" }) end end
	-- Reachable notables and keystones, with the points their path costs
	for id, node in pairs(build.spec.nodes) do
		if (node.type == "Notable" or node.type == "Keystone") and not node.alloc and not node.ascendancyName and node.path and #node.path <= (p.maxPath or 6) then
			table.insert(result.passives, { id = id, name = node.dn, type = node.type, cost = #node.path })
		end
	end
	-- Allocated notables / keystones that can be removed without disconnecting more than a few points
	result.removable = { }
	for id, node in pairs(build.spec.allocNodes) do
		if (node.type == "Notable" or node.type == "Keystone") and not node.ascendancyName then
			table.insert(result.removable, { id = id, name = node.dn, frees = #(node.depends or { node }) })
		end
	end
	-- Uniques per equipped slot, within the character's level
	local level = build.characterLevel
	for _, slot in ipairs(build.itemsTab.orderedSlots or { }) do
		local slotName = slot.slotName
		if not slotName:match("^Flask") and not slotName:match("^Jewel") and not slotName:match("Abyssal") and slot:IsShown() ~= false
			and not (p.lockedSlots or { })[slotName] then
			local list = { }
			local current = slot.selItemId and build.itemsTab.items[slot.selItemId]
			if not current then
				-- Only slots the build uses (e.g. no off-hand with a two-handed weapon)
				goto nextSlot
			end
			for _, item in pairs(main.uniqueDB.list) do
				local primary = item:GetPrimarySlot()
				if primary and (primary == slotName or primary:gsub(" %d$", "") == slotName:gsub(" %d$", ""))
					and (item.requirements.level or 0) <= level and (not current or item.title ~= current.title) then
					table.insert(list, item.title)
				end
			end
			table.sort(list)
			result.uniques[slotName] = list
		end
		::nextSlot::
	end
	result.points = { pointBudget() }
	return result
end

-- The build with changes applied, as a PoB build file (open it in Path of Building)
function methods.export(p)
	dirty = true
	loadFresh(p)
	selectMain(p)
	local applied = { }
	for _, change in ipairs(p.changes or { }) do table.insert(applied, changeHandlers[change.type](change)) end
	recalc()
	local inferred = applyInference(p)
	if p.notes and build.notesTab and build.notesTab.controls.edit then
		build.notesTab.controls.edit:SetText(p.notes)
	end
	local m = extendedMetrics()
	return { xml = build:SaveDB("export"), metrics = m, applied = applied, inferred = inferred }
end

-- Mercenary roster: classes with their fixed skill pools (src/Data/Mercenaries.lua)
function methods.mercenaries(p)
	return Merc.describe(p.class)
end

-- Mechanics knowledge base entries, with the uniques and passives that carry each mechanic
function methods.mechanics(p)
	local want = p.id and p.id:lower()
	local query = p.query and p.query:lower()
	local tree = main:LoadTree(latestTreeVersion)
	local results = { }
	for _, mech in ipairs(autoTags.GetMechanics()) do
		local text = (mech.id .. " " .. mech.label .. " " .. (mech.summary or "")):lower()
		if (not want or mech.id == want or mech.label:lower() == want) and (not query or text:find(query, 1, true)) then
			local entry = copyTable(mech)
			entry.detect = nil
			local tagId = mech.tag or mech.id
			if autoTags.GetTagDef(tagId) then
				local uniques, passives = { }, { }
				for _, item in pairs(main.uniqueDB.list) do
					if autoTags.GetItemTags(item)[tagId] then table.insert(uniques, item.title or item.name) end
				end
				for _, node in pairs(tree.nodes) do
					if node.dn and (node.type == "Notable" or node.type == "Keystone" or node.ascendancyName) and node.type ~= "AscendClassStart"
						and autoTags.GetNodeTags(node)[tagId] then
						table.insert(passives, node.ascendancyName and (node.dn .. " (" .. node.ascendancyName .. ")") or node.dn)
					end
				end
				table.sort(uniques)
				table.sort(passives)
				entry.uniques, entry.passives = uniques, passives
			end
			table.insert(results, entry)
		end
	end
	return results
end

function methods.list_tags()
	local list = { }
	for _, def in ipairs(autoTags.GetTagList()) do
		table.insert(list, { id = def.id, label = def.label, category = def.category, parent = def.parent })
	end
	return list
end

local function respond(tbl)
	io.stdout:write("@@RESP " .. dkjson.encode(tbl) .. "\n")
	io.stdout:flush()
end

io.stdout:write("@@READY\n")
io.stdout:flush()
for line in io.stdin:lines() do
	if line:match("%S") then
		local req, _, err = dkjson.decode(line)
		if not req then
			respond({ ok = false, error = "bad request: " .. tostring(err) })
		else
			local method = methods[req.method or ""]
			if not method then
				respond({ id = req.id, ok = false, error = "unknown method '" .. tostring(req.method) .. "'" })
			else
				local ok, result = pcall(method, req.params or { })
				if ok then
					respond({ id = req.id, ok = true, result = result })
				else
					dirty = true
					respond({ id = req.id, ok = false, error = (tostring(result):gsub("^.-%.lua:%d+: ", "")) })
				end
			end
		end
	end
end
