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
local round = S.round

local loadedXml, dirty = nil, true

local function ensureBuild(params)
	assert(params.xml, "missing build xml")
	if dirty or loadedXml ~= params.xml then
		loadBuildFromXML(params.xml, params.name or "build")
		loadedXml, dirty = params.xml, false
	end
end

local function recalc()
	build.buildFlag = true
	runCallback("OnFrame")
	return build.calcsTab.mainOutput
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

local function metrics()
	local o = build.calcsTab.mainOutput
	local env = build.calcsTab.mainEnv
	local skill = env.player.mainSkill
	local m = {
		mainGroup = build.mainSocketGroup,
		mainSkill = skill and skill.activeEffect.grantedEffect.name,
		playerDPS = round(o.CombinedDPS or 0, 1),
		minionDPS = o.Minion and round(o.Minion.CombinedDPS or 0, 1) or nil,
	}
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

function methods.metrics(p)
	ensureBuild(p)
	if p.group then
		local _, index = findGroup(p.group)
		build.mainSocketGroup = index
		recalc()
	else
		primaryGroup()
	end
	return metrics()
end

function methods.simulate(p)
	dirty = true
	ensureBuild(p)
	if p.group then
		local _, index = findGroup(p.group)
		build.mainSocketGroup = index
		recalc()
	else
		primaryGroup()
	end
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
	local after = metrics()
	local diff = { }
	for key, value in pairs(after) do
		if type(value) == "number" and type(before[key]) == "number" and value ~= before[key] then
			diff[key] = { before = before[key], after = value, change = round(value - before[key], 2),
				percent = before[key] ~= 0 and round((value / before[key] - 1) * 100, 1) or nil }
		end
	end
	dirty = true
	return { applied = applied, before = before, after = after, changed = diff }
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
