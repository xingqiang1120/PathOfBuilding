-- Path of Building
--
-- Module: Auto Tags
-- Derives structured, build-archetype tags (Minion, Totem, Fire, Life, ...) for items and passive
-- nodes from their parsed modifiers, and layers manual tags on top.
--
-- Layers, applied in order:
--   1. Rules            Data/AutoTagRules.lua      (derived from parsed modifiers)
--   2. Shipped overrides Data/AutoTagOverrides.lua (curated, versioned with the code)
--   3. User overrides   <userPath>/AutoTags.xml    (edited in-app with Ctrl+T)
-- Tags may have a parent; a tag always implies its parent (e.g. Zombie -> Minion).
--
local pairs = pairs
local ipairs = ipairs
local type = type
local t_insert = table.insert
local t_sort = table.sort
local band = bit.band
local bnot = bit.bnot

autoTags = { }

local matchAllMask = bnot(KeywordFlag.MatchAll)

local ruleList = { }
local tagById = { }
local tagOrder = { }
local baseOverrides = { item = { }, node = { } }
local userOverrides = { item = { }, node = { } }
local userTagIds = { }
local generation = 0

local function toSet(list, lower)
	local set = { }
	for _, v in ipairs(list or { }) do
		set[lower and v:lower() or v] = true
	end
	return set
end

local function bump()
	generation = generation + 1
end

---Changes whenever rules, overrides or user tags change; use it to invalidate cached UI state.
function autoTags.GetGeneration()
	return generation
end

local function addTag(def)
	if not tagById[def.id] then
		t_insert(tagOrder, def.id)
	end
	tagById[def.id] = def
end

---Normalise a free-form tag name to a tag id ("Summon Raging Spirit" -> "summonragingspirit").
function autoTags.NormaliseId(name)
	return (name:lower():gsub("[^%w]", ""))
end

---Initialise (or re-initialise) the tagger. Clears all overrides, including user ones.
---@param rules table @List of rules, see Data/AutoTagRules.lua
---@param overrides table? @See Data/AutoTagOverrides.lua
local mechanicList, mechanicById = { }, { }

local function compileRule(rule)
	return {
		id = rule.id,
		parent = rule.parent,
		minionToo = rule.minionToo,
		modNames = rule.modNames or { },
		modPatterns = rule.modPatterns or { },
		excludePatterns = rule.excludePatterns or { },
		modFlags = rule.modFlags or 0,
		keywordFlags = band(rule.keywordFlags or 0, matchAllMask),
		skillTypes = toSet(rule.skillTypes),
		skillNames = toSet(rule.skillNames, true),
		gemKeywords = rule.gemKeywords or { },
		textPatterns = rule.textPatterns or { },
		textAlways = rule.textAlways,
	}
end

---Initialise (or re-initialise) the tagger. Clears all overrides, including user ones.
---@param rules table @List of rules, see Data/AutoTagRules.lua
---@param overrides table? @See Data/AutoTagOverrides.lua
---@param mechanics table? @See Data/Mechanics.lua (loaded when omitted)
function autoTags.Init(rules, overrides, mechanics)
	ruleList = { }
	tagById = { }
	tagOrder = { }
	baseOverrides = { item = { }, node = { } }
	userOverrides = { item = { }, node = { } }
	userTagIds = { }
	bump()
	for _, rule in ipairs(rules) do
		t_insert(ruleList, compileRule(rule))
		addTag({ id = rule.id, label = rule.label or rule.id, category = rule.category or "Other", parent = rule.parent })
	end
	-- Mechanics become tags too, and carry the tags they imply (e.g. withered -> chaos)
	mechanicList, mechanicById = mechanics or LoadModule("Data/Mechanics"), { }
	for _, mech in ipairs(mechanicList) do
		mechanicById[mech.id] = mech
		if mech.detect then
			local rule = copyTable(mech.detect, true)
			rule.id = mech.id
			t_insert(ruleList, compileRule(rule))
			addTag({ id = mech.id, label = mech.label, category = "Mechanic" })
		end
	end
	for _, mech in ipairs(mechanicList) do
		local def = tagById[mech.tag or mech.id]
		if def then
			def.implies = mech.implies
			def.mechanic = mech.id
		end
	end
	autoTags.AddOverrides(overrides)
end

---Mechanics knowledge base entries (Data/Mechanics.lua).
function autoTags.GetMechanics()
	return mechanicList
end

function autoTags.GetMechanic(id)
	return mechanicById[id]
end

local function mergeEntries(dest, src)
	for key, entry in pairs(src or { }) do
		local cur = dest[key] or { add = { }, remove = { } }
		for _, id in ipairs(entry.add or { }) do cur.add[id] = true end
		for _, id in ipairs(entry.remove or { }) do cur.remove[id] = true end
		dest[key] = cur
	end
end

---Merge additional curated overrides into the shipped layer.
function autoTags.AddOverrides(overrides)
	if not overrides then
		return
	end
	bump()
	for _, def in ipairs(overrides.tags or { }) do
		addTag({ id = def.id, label = def.label or def.id, category = def.category or "Custom", parent = def.parent })
	end
	mergeEntries(baseOverrides.item, overrides.items)
	mergeEntries(baseOverrides.node, overrides.nodes)
end

-- Rule matching

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

local function grantedSkill(mod)
	if (mod.name == "ExtraSkill" or mod.name == "ExtraSupport") and type(mod.value) == "table" and mod.value.skillId then
		return data.skills[mod.value.skillId]
	end
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
	local granted = grantedSkill(mod)
	if next(rule.skillTypes) then
		for _, tag in ipairs(mod) do
			if tag.type == "SkillType" and tag.skillType and rule.skillTypes[tag.skillType] then
				return true
			end
		end
		if granted and granted.skillTypes then
			for skillType in pairs(rule.skillTypes) do
				if granted.skillTypes[skillType] then
					return true
				end
			end
		end
	end
	if next(rule.skillNames) then
		for _, tag in ipairs(mod) do
			if tag.type == "SkillName" then
				if tag.skillName and rule.skillNames[tag.skillName:lower()] then
					return true
				end
				for _, name in ipairs(tag.skillNameList or { }) do
					if rule.skillNames[name:lower()] then
						return true
					end
				end
			end
		end
		if granted and granted.name and rule.skillNames[granted.name:lower()] then
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
		-- Effects applied to minions describe the minions, not the player: only the minion tag, its
		-- sub-tags (minion types) and mechanics marked minionToo (e.g. Unholy Might) are considered
		out.minion = true
		local inner = type(mod.value) == "table" and mod.value.mod
		for _, rule in ipairs(ruleList) do
			if (rule.parent == "minion" or rule.minionToo) and not out[rule.id] and (ruleMatchesMod(rule, mod) or (inner and ruleMatchesMod(rule, inner))) then
				out[rule.id] = true
			end
		end
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
---@param text string? @Display text of the line; used for unparsed lines and textAlways rules
function autoTags.GetLineTags(modList, extra, text, out)
	out = out or { }
	local parsed = modList and modList[1] and not extra
	if modList then
		for _, mod in ipairs(modList) do
			autoTags.GetModTags(mod, out)
		end
	end
	if text then
		local lower = text:lower()
		for _, rule in ipairs(ruleList) do
			if not out[rule.id] and (rule.textAlways or not parsed) then
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

-- Applying layers

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

-- Add parent tags and implied tags until nothing changes. New keys are collected first: adding
-- keys to a table while traversing it with pairs is undefined in Lua.
local function expandParents(tags)
	local changed = true
	while changed do
		changed = false
		local add = { }
		for id in pairs(tags) do
			local def = tagById[id]
			if def then
				if def.parent and not tags[def.parent] then
					t_insert(add, def.parent)
				end
				for _, implied in ipairs(def.implies or { }) do
					if not tags[implied] and tagById[implied] then
						t_insert(add, implied)
					end
				end
			end
		end
		for _, id in ipairs(add) do
			if not tags[id] then
				tags[id] = true
				changed = true
			end
		end
	end
	return tags
end

local itemLineGroups = { "enchantModLines", "scourgeModLines", "implicitModLines", "explicitModLines", "crucibleModLines" }

local function getModLineTags(modLine)
	local cache = modLine.autoTagCache
	if cache and cache.line == modLine.line and cache.ruleGeneration == ruleList then
		return cache.tags
	end
	local tags = autoTags.GetLineTags(modLine.modList, modLine.extra, modLine.line)
	modLine.autoTagCache = { line = modLine.line, ruleGeneration = ruleList, tags = tags }
	return tags
end

---Key under which manual tags for an item are stored.
function autoTags.GetItemKey(item)
	return item.title or item.name
end

---Key under which manual tags for a passive node are stored.
function autoTags.GetNodeKey(node)
	return node.id
end

---Tags derived from rules only, honouring the item's currently selected variant(s).
function autoTags.GetItemRuleTags(item)
	local tags = { }
	for _, group in ipairs(itemLineGroups) do
		for _, modLine in ipairs(item[group] or { }) do
			if not modLine.disabled and (not item.CheckModLineVariant or item:CheckModLineVariant(modLine)) then
				mergeSet(tags, getModLineTags(modLine))
			end
		end
	end
	return tags
end

---Get the full tag set of an item (rules + shipped overrides + user overrides, parents expanded).
---@return table<string, boolean>
function autoTags.GetItemTags(item)
	local tags = autoTags.GetItemRuleTags(item)
	local key = autoTags.GetItemKey(item)
	if key then
		applyOverride(tags, baseOverrides.item[key])
		applyOverride(tags, userOverrides.item[key])
	end
	return expandParents(tags)
end

---Tags derived from rules only. Masteries are tagged with the union of all their effects.
function autoTags.GetNodeRuleTags(node)
	local cache = node.autoTagRuleCache
	if cache and cache.modList == node.modList and cache.ruleGeneration == ruleList then
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
	node.autoTagRuleCache = { modList = node.modList, ruleGeneration = ruleList, tags = tags }
	return tags
end

---Get the full tag set of a passive node.
---@return table<string, boolean>
function autoTags.GetNodeTags(node)
	local cache = node.autoTagCache
	if cache and cache.modList == node.modList and cache.generation == generation then
		return cache.tags
	end
	local tags = copyTable(autoTags.GetNodeRuleTags(node), true)
	applyOverride(tags, baseOverrides.node[node.id] or baseOverrides.node[node.dn])
	applyOverride(tags, userOverrides.node[node.id])
	expandParents(tags)
	node.autoTagCache = { modList = node.modList, generation = generation, tags = tags }
	return tags
end

-- Queries

---Returns true if tags contains every id in required.
function autoTags.HasAll(tags, required)
	for _, id in ipairs(required) do
		if not tags[id] then
			return false
		end
	end
	return true
end

---Find a tag id by id, label or normalised label.
function autoTags.FindTag(word)
	word = word:lower():gsub("^%s+", ""):gsub("%s+$", "")
	if tagById[word] then
		return word
	end
	local norm = autoTags.NormaliseId(word)
	for _, id in ipairs(tagOrder) do
		local label = tagById[id].label:lower()
		if label == word or autoTags.NormaliseId(label) == norm then
			return id
		end
	end
end

---Resolve a comma separated list of tag ids or labels ("minion, fire") to tag ids.
---@return string[] ids, string[] unknown
function autoTags.ParseQuery(str)
	local ids, unknown = { }, { }
	for word in str:gmatch("[^,]+") do
		word = word:gsub("^%s+", ""):gsub("%s+$", "")
		if word ~= "" then
			local id = autoTags.FindTag(word)
			if id then
				t_insert(ids, id)
			else
				t_insert(unknown, word:lower())
			end
		end
	end
	return ids, unknown
end

function autoTags.GetTagDef(id)
	return tagById[id]
end

---Ordered list of tag definitions; sub-tags follow their parent.
function autoTags.GetTagList()
	local list = { }
	local children = { }
	for _, id in ipairs(tagOrder) do
		local def = tagById[id]
		if def.parent and tagById[def.parent] then
			children[def.parent] = children[def.parent] or { }
			t_insert(children[def.parent], def)
		end
	end
	local function add(def, depth)
		t_insert(list, def)
		def.depth = depth
		for _, child in ipairs(children[def.id] or { }) do
			add(child, depth + 1)
		end
	end
	for _, id in ipairs(tagOrder) do
		local def = tagById[id]
		if not (def.parent and tagById[def.parent]) then
			add(def, 0)
		end
	end
	return list
end

---Human readable, ordered list of labels for a tag set.
function autoTags.Describe(tags)
	local labels = { }
	for _, def in ipairs(autoTags.GetTagList()) do
		if tags[def.id] then
			t_insert(labels, def.label)
		end
	end
	return labels
end

---Tooltip lines for a tag set, wrapped; custom (user) tags are highlighted.
function autoTags.FormatTooltipLines(tags, maxChars)
	maxChars = maxChars or 70
	local lines, cur, curLen = { }, "^8Tags: ", 6
	local any = false
	for _, def in ipairs(autoTags.GetTagList()) do
		if tags[def.id] then
			local text = def.label
			if any and curLen + #text + 2 > maxChars then
				t_insert(lines, cur .. "^8,")
				cur, curLen = "^8      ", 6
			elseif any then
				cur, curLen = cur .. "^8, ", curLen + 2
			end
			cur = cur .. (def.user and "^xE0C060" or "^8") .. text
			curLen = curLen + #text
			any = true
		end
	end
	if not any then
		cur = cur .. "(none)"
	end
	t_insert(lines, cur)
	return lines
end

-- User layer

---Define (or update) a user tag. Returns its id.
function autoTags.DefineUserTag(label, parent)
	local id = autoTags.NormaliseId(label)
	if id == "" then
		return
	end
	local def = tagById[id]
	if def and not userTagIds[id] then
		-- Existing built-in tag; never redefine it
		return id
	end
	addTag({ id = id, label = def and def.label or label, category = "Custom", parent = parent or (def and def.parent), user = true })
	userTagIds[id] = true
	bump()
	return id
end

---List of user-defined tag definitions.
function autoTags.GetUserTags()
	local list = { }
	for _, id in ipairs(tagOrder) do
		if userTagIds[id] then
			t_insert(list, tagById[id])
		end
	end
	return list
end

---Parse the editor syntax: "Minion/My Zombies, srs, -life".
---  name          add an existing tag, or create a new custom tag
---  Parent/Child  add Child as a sub-tag of Parent (Parent is created if needed)
---  -name         remove a tag that rules or shipped overrides added
---@return string[] add, string[] remove
function autoTags.ParseEditString(str)
	local add, remove = { }, { }
	for word in str:gmatch("[^,]+") do
		word = word:gsub("^%s+", ""):gsub("%s+$", "")
		local negate = word:match("^%-%s*(.+)$")
		if negate then
			local id = autoTags.FindTag(negate)
			if id then
				t_insert(remove, id)
			end
		elseif word ~= "" then
			local parentName, childName = word:match("^(.-)%s*/%s*(.+)$")
			local id
			if parentName and parentName ~= "" then
				local parentId = autoTags.FindTag(parentName) or autoTags.DefineUserTag(parentName)
				id = autoTags.FindTag(childName)
				if not id or userTagIds[id] then
					id = autoTags.DefineUserTag(childName, parentId)
				end
			else
				id = autoTags.FindTag(word) or autoTags.DefineUserTag(word)
			end
			if id then
				t_insert(add, id)
			end
		end
	end
	return add, remove
end

---Format the user entry of an item or node in editor syntax.
function autoTags.FormatEditString(kind, key)
	local entry = userOverrides[kind][key]
	if not entry then
		return ""
	end
	local parts = { }
	for _, def in ipairs(autoTags.GetTagList()) do
		if entry.add[def.id] then
			local parent = def.user and def.parent and tagById[def.parent]
			t_insert(parts, parent and (parent.label .. "/" .. def.label) or def.label)
		end
	end
	for _, def in ipairs(autoTags.GetTagList()) do
		if entry.remove[def.id] then
			t_insert(parts, "-" .. def.label)
		end
	end
	return table.concat(parts, ", ")
end

---Replace the user tags of an item ("item") or passive node ("node").
function autoTags.SetUserEntry(kind, key, add, remove)
	if not next(add or { }) and not next(remove or { }) then
		userOverrides[kind][key] = nil
	else
		userOverrides[kind][key] = { add = toSet(add), remove = toSet(remove), name = userOverrides[kind][key] and userOverrides[kind][key].name }
	end
	bump()
end

---Remember a readable name for a user entry (stored in the file for humans; nodes are keyed by id).
function autoTags.SetUserEntryName(kind, key, name)
	if userOverrides[kind][key] then
		userOverrides[kind][key].name = name
	end
end

local function idList(set)
	local list = { }
	for id in pairs(set) do
		t_insert(list, id)
	end
	t_sort(list)
	return table.concat(list, ",")
end

local function splitIds(str)
	local list = { }
	for id in (str or ""):gmatch("[^,]+") do
		t_insert(list, id)
	end
	return list
end

---Load user tags from an XML file. Missing files are ignored.
function autoTags.LoadUserFile(path)
	autoTags.userFilePath = path
	local root = common.xml.LoadXMLFile(path)
	if not root or not root[1] or root[1].elem ~= "AutoTags" then
		return
	end
	for _, node in ipairs(root[1]) do
		if type(node) == "table" and node.attrib then
			if node.elem == "Tag" and node.attrib.label then
				local parent = node.attrib.parent ~= "" and node.attrib.parent or nil
				autoTags.DefineUserTag(node.attrib.label, parent)
			end
		end
	end
	for _, node in ipairs(root[1]) do
		if type(node) == "table" and node.attrib then
			local kind = node.elem == "Item" and "item" or node.elem == "Node" and "node"
			local key = kind == "item" and node.attrib.name or kind == "node" and tonumber(node.attrib.id)
			if key then
				autoTags.SetUserEntry(kind, key, splitIds(node.attrib.add), splitIds(node.attrib.remove))
				if kind == "node" then
					autoTags.SetUserEntryName(kind, key, node.attrib.name)
				end
			end
		end
	end
end

---Save user tags to an XML file (defaults to the file they were loaded from).
function autoTags.SaveUserFile(path)
	path = path or autoTags.userFilePath
	if not path then
		return
	end
	local root = { elem = "AutoTags" }
	for _, def in ipairs(autoTags.GetUserTags()) do
		t_insert(root, { elem = "Tag", attrib = { id = def.id, label = def.label, parent = def.parent } })
	end
	local function addEntries(kind, elem)
		local keys = { }
		for key in pairs(userOverrides[kind]) do
			t_insert(keys, key)
		end
		t_sort(keys, function(a, b) return tostring(a) < tostring(b) end)
		for _, key in ipairs(keys) do
			local entry = userOverrides[kind][key]
			local attrib = { add = idList(entry.add), remove = idList(entry.remove) }
			if kind == "item" then
				attrib.name = key
			else
				attrib.id = tostring(key)
				attrib.name = entry.name
			end
			t_insert(root, { elem = elem, attrib = attrib })
		end
	end
	addEntries("item", "Item")
	addEntries("node", "Node")
	return common.xml.SaveXMLFile(root, path)
end

autoTags.Init(LoadModule("Data/AutoTagRules"), LoadModule("Data/AutoTagOverrides"))
