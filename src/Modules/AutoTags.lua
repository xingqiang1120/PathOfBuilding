-- Path of Building
--
-- Module: Auto Tags
-- Derives structured, build-archetype tags (Minion, Totem, Fire, Life, ...) for items and passive
-- nodes from their parsed modifiers. Rules live in Data/AutoTagRules.lua, manual additions in
-- Data/AutoTagOverrides.lua.
--
local pairs = pairs
local ipairs = ipairs
local type = type
local t_insert = table.insert
local band = bit.band
local bnot = bit.bnot

autoTags = { }

local matchAllMask = bnot(KeywordFlag.MatchAll)

local ruleList = { }
local tagById = { }
local tagOrder = { }
local itemOverrides = { }
local nodeOverrides = { }
local generation = 0

local function toSet(list)
	local set = { }
	for _, v in ipairs(list or { }) do
		set[v] = true
	end
	return set
end

local function addTag(def)
	if not tagById[def.id] then
		t_insert(tagOrder, def.id)
	end
	tagById[def.id] = def
end

---Initialise (or re-initialise) the tagger.
---@param rules table @List of rules, see Data/AutoTagRules.lua
---@param overrides table? @See Data/AutoTagOverrides.lua
function autoTags.Init(rules, overrides)
	ruleList = { }
	tagById = { }
	tagOrder = { }
	itemOverrides = { }
	nodeOverrides = { }
	generation = generation + 1
	for _, rule in ipairs(rules) do
		local compiled = {
			id = rule.id,
			modNames = rule.modNames or { },
			modPatterns = rule.modPatterns or { },
			excludePatterns = rule.excludePatterns or { },
			modFlags = rule.modFlags or 0,
			keywordFlags = band(rule.keywordFlags or 0, matchAllMask),
			skillTypes = toSet(rule.skillTypes),
			gemKeywords = rule.gemKeywords or { },
			textPatterns = rule.textPatterns or { },
		}
		t_insert(ruleList, compiled)
		addTag({ id = rule.id, label = rule.label or rule.id, category = rule.category or "Other" })
	end
	autoTags.AddOverrides(overrides)
end

---Merge additional manual overrides (e.g. from a user file) into the current state.
function autoTags.AddOverrides(overrides)
	if not overrides then
		return
	end
	generation = generation + 1
	for _, def in ipairs(overrides.tags or { }) do
		addTag({ id = def.id, label = def.label or def.id, category = def.category or "Custom", parent = def.parent })
	end
	local function merge(dest, src)
		for key, entry in pairs(src or { }) do
			local cur = dest[key] or { add = { }, remove = { } }
			for _, id in ipairs(entry.add or { }) do cur.add[id] = true end
			for _, id in ipairs(entry.remove or { }) do cur.remove[id] = true end
			dest[key] = cur
		end
	end
	merge(itemOverrides, overrides.items)
	merge(nodeOverrides, overrides.nodes)
end

local function nameMatches(rule, name)
	local hit = rule.modNames[name]
	if not hit then
		for _, pattern in ipairs(rule.modPatterns) do
			if name:match(pattern) then
				hit = true
				break
			end
		end
	end
	if hit then
		for _, pattern in ipairs(rule.excludePatterns) do
			if name:match(pattern) then
				return false
			end
		end
	end
	return hit
end

local function skillMatches(rule, skillId)
	local grantedEffect = skillId and data.skills[skillId]
	if grantedEffect and grantedEffect.skillTypes then
		for skillType in pairs(rule.skillTypes) do
			if grantedEffect.skillTypes[skillType] then
				return true
			end
		end
	end
	return false
end

local function ruleMatchesMod(rule, mod)
	if nameMatches(rule, mod.name) then
		return true
	end
	if rule.modFlags ~= 0 and mod.flags and band(mod.flags, rule.modFlags) ~= 0 then
		return true
	end
	if rule.keywordFlags ~= 0 and mod.keywordFlags and band(mod.keywordFlags, rule.keywordFlags) ~= 0 then
		return true
	end
	if next(rule.skillTypes) then
		for _, tag in ipairs(mod) do
			if tag.type == "SkillType" and tag.skillType and rule.skillTypes[tag.skillType] then
				return true
			end
		end
		if (mod.name == "ExtraSkill" or mod.name == "ExtraSupport") and type(mod.value) == "table" and skillMatches(rule, mod.value.skillId) then
			return true
		end
	end
	if mod.name == "GemProperty" and type(mod.value) == "table" then
		if mod.value.keyword and rule.gemKeywords[mod.value.keyword] then
			return true
		end
		for _, keyword in ipairs(mod.value.keywordList or { }) do
			if rule.gemKeywords[keyword] then
				return true
			end
		end
	end
	return false
end

---Add the tags of a single parsed modifier to out.
function autoTags.GetModTags(mod, out)
	out = out or { }
	if mod.name == "MinionModifier" or mod.name == "MinionPerSkillModifier" then
		-- Effects applied to minions describe the minions, not the player
		out.minion = true
		return out
	end
	for _, rule in ipairs(ruleList) do
		if not out[rule.id] and ruleMatchesMod(rule, mod) then
			out[rule.id] = true
		end
	end
	return out
end

---Add the tags of one modifier line to out.
---@param modList table? @Parsed mods of the line
---@param extra any @Unparsed remainder reported by the mod parser
---@param text string? @Display text of the line, used as fallback for unparsed lines
function autoTags.GetLineTags(modList, extra, text, out)
	out = out or { }
	local parsed = modList and modList[1] and not extra
	if modList then
		for _, mod in ipairs(modList) do
			autoTags.GetModTags(mod, out)
		end
	end
	if not parsed and text then
		local lower = text:lower()
		for _, rule in ipairs(ruleList) do
			if not out[rule.id] then
				for _, pattern in ipairs(rule.textPatterns) do
					if lower:find(pattern) then
						out[rule.id] = true
						break
					end
				end
			end
		end
	end
	return out
end

local function mergeSet(dest, src)
	for id in pairs(src) do
		dest[id] = true
	end
end

local function applyOverride(tags, override)
	if override then
		for id in pairs(override.remove) do tags[id] = nil end
		for id in pairs(override.add) do tags[id] = true end
	end
end

local function expandParents(tags)
	local changed = true
	while changed do
		changed = false
		for id in pairs(tags) do
			local def = tagById[id]
			if def and def.parent and not tags[def.parent] then
				tags[def.parent] = true
				changed = true
			end
		end
	end
	return tags
end

local itemLineGroups = { "enchantModLines", "scourgeModLines", "implicitModLines", "explicitModLines", "crucibleModLines" }

local function getModLineTags(modLine)
	if modLine.autoTagCache and modLine.autoTagCache.line == modLine.line and modLine.autoTagCache.generation == generation then
		return modLine.autoTagCache.tags
	end
	local tags = autoTags.GetLineTags(modLine.modList, modLine.extra, modLine.line)
	modLine.autoTagCache = { line = modLine.line, generation = generation, tags = tags }
	return tags
end

---Get the tag set of an item, honouring its currently selected variant(s).
---@return table<string, boolean>
function autoTags.GetItemTags(item)
	local tags = { }
	for _, group in ipairs(itemLineGroups) do
		for _, modLine in ipairs(item[group] or { }) do
			if not modLine.disabled and (not item.CheckModLineVariant or item:CheckModLineVariant(modLine)) then
				mergeSet(tags, getModLineTags(modLine))
			end
		end
	end
	applyOverride(tags, itemOverrides[item.title or item.name])
	return expandParents(tags)
end

---Get the tag set of a passive node. Masteries are tagged with the union of all their effects.
---@return table<string, boolean>
function autoTags.GetNodeTags(node)
	local cache = node.autoTagCache
	if cache and cache.modList == node.modList and cache.generation == generation then
		return cache.tags
	end
	local tags = { }
	if node.type == "Mastery" and node.masteryEffects then
		for _, effect in ipairs(node.masteryEffects) do
			for _, line in ipairs(effect.stats or { }) do
				local modList, extra = modLib.parseMod(line)
				autoTags.GetLineTags(modList, extra, line, tags)
			end
		end
	end
	for index, line in ipairs(node.sd or { }) do
		local mods = node.mods and node.mods[index]
		autoTags.GetLineTags(mods and mods.list, mods and mods.extra, line, tags)
	end
	applyOverride(tags, nodeOverrides[node.id] or nodeOverrides[node.dn])
	expandParents(tags)
	node.autoTagCache = { modList = node.modList, generation = generation, tags = tags }
	return tags
end

---Returns true if tags contains every id in required.
function autoTags.HasAll(tags, required)
	for _, id in ipairs(required) do
		if not tags[id] then
			return false
		end
	end
	return true
end

---Resolve a comma or space separated list of tag ids or labels ("minion, fire") to tag ids.
---@return string[] ids, string[] unknown
function autoTags.ParseQuery(str)
	local ids, unknown = { }, { }
	for word in str:lower():gmatch("[^,]+") do
		word = word:gsub("^%s+", ""):gsub("%s+$", "")
		if word ~= "" then
			local found
			for _, id in ipairs(tagOrder) do
				local label = tagById[id].label:lower()
				if id == word or label == word or label:gsub("[^%w]", "") == word:gsub("[^%w]", "") then
					found = id
					break
				end
			end
			if found then
				t_insert(ids, found)
			else
				t_insert(unknown, word)
			end
		end
	end
	return ids, unknown
end

function autoTags.GetTagDef(id)
	return tagById[id]
end

---Ordered list of tag definitions, grouped by category in declaration order.
function autoTags.GetTagList()
	local list = { }
	for _, id in ipairs(tagOrder) do
		t_insert(list, tagById[id])
	end
	return list
end

---Human readable, ordered list of labels for a tag set.
function autoTags.Describe(tags)
	local labels = { }
	for _, id in ipairs(tagOrder) do
		if tags[id] then
			t_insert(labels, tagById[id].label)
		end
	end
	return labels
end

autoTags.Init(LoadModule("Data/AutoTagRules"), LoadModule("Data/AutoTagOverrides"))
