-- Path of Building
--
-- Luminary mercenary model. PoB has no mercenary; its Party tab already handles an ally's auras
-- (with their effect, on you and your minions) and curses (sharing the enemy's curse slots with
-- yours and your minions'). The mercenary is modelled as that party member:
--
--   1. its skills are calculated in a throw-away PoB build with the gem versions of the skills,
--      whose Party export gives the aura and curse buffs in PoB's own text format;
--   2. the player's own "increased effect of Non-Curse Auras" on the mercenary (Bestowed Knighthood),
--      extra aura effect and mercenary-exclusive supports (Curse Effect III) are added to the effects;
--   3. the text goes into the player build's Party tab, so it is also saved with the build and
--      visible in the PoB GUI;
--   4. the mercenary's Life goes into Config (TotalMercenaryLife) for Loyal Bodyguard.
--
-- spec, by class (src/Data/Mercenaries.lua: fixed skill pools per class):
--   { class = "Cruel Mistress", skills = { "Zealotry", "Envy", "Dark Bargain", "Profane Cascade" },
--     supports = { Despair = { "Curse Effect III" } }, levels = { Zealotry = 20 }, life = 8000 }
--   Primary skills are always included; skills lists the rolled secondary and utility skills.
-- or explicit (any skills):
--   { auras = { { name = "Zealotry", level = 20 } }, curses = { { name = "Despair", level = 20 } }, life = 8000 }
-- common fields: auraEffect (extra % on the mercenary's auras), life, level, includeVaal (Vaal auras)
--
-- Mercenary skills are not gems; their numbers may differ and ignore gem level and quality (PoE Wiki).
-- Gem level 20, quality 0 is used as an estimate unless levels says otherwise.

local Roster = LoadModule("Data/Mercenaries")

local M = { roster = Roster }

local cache = { }

local function xmlEscape(s)
	return (tostring(s):gsub("&", "&amp;"):gsub('"', "&quot;"):gsub("<", "&lt;"):gsub(">", "&gt;"))
end

-- A skill that is a gem by that exact name, or a skill only granted by items (e.g. Envy)
local function classify(name)
	for _, gem in pairs(data.gems) do
		if gem.name == name and not gem.grantedEffect.support then
			return "gem", gem.name
		end
	end
	for _, skill in pairs(data.skills) do
		-- Hidden skills granted by items (fromItem) are fine; other hidden skills are internal
		if skill.name == name and not skill.support and (not skill.hidden or skill.fromItem) then
			return "granted", skill.name
		end
	end
	error("unknown mercenary skill '" .. tostring(name) .. "'", 0)
end

local function findIn(list, name)
	for _, entry in ipairs(list) do
		if entry:lower() == name:lower() then
			return entry
		end
	end
end

---Turn a class-based spec into the explicit form. Explicit specs pass through.
---@return table explicit spec, table report { class, skills, unmodelled, warnings }
function M.resolve(spec)
	local report = { warnings = { }, unmodelled = { }, estimated = { } }
	if not spec.class then
		return spec, report
	end
	local class = Roster.byName[spec.class:lower()]
	if not class then
		local names = { }
		for _, c in ipairs(Roster.classes) do table.insert(names, c.name) end
		error("unknown mercenary class '" .. spec.class .. "' (classes: " .. table.concat(names, ", ") .. ")", 0)
	end
	report.class = class.name
	local chosen, counts = { }, { secondary = 0, utility = 0 }
	for _, name in ipairs(class.primary) do
		table.insert(chosen, name)
	end
	for _, want in ipairs(spec.skills or { }) do
		local found
		for _, pool in ipairs({ "secondary", "utility" }) do
			found = findIn(class[pool].options, want)
			if found then
				counts[pool] = counts[pool] + 1
				break
			end
		end
		if not found and not findIn(class.primary, want) then
			error(string.format("%s cannot roll '%s' (secondary: %s; utility: %s)", class.name, want,
				table.concat(class.secondary.options, ", "), table.concat(class.utility.options, ", ")), 0)
		end
		if found then
			table.insert(chosen, found)
		end
	end
	for _, pool in ipairs({ "secondary", "utility" }) do
		if counts[pool] > class[pool].pick then
			table.insert(report.warnings, string.format("%s rolls %d %s skill(s), %d given", class.name, class[pool].pick, pool, counts[pool]))
		end
	end
	report.skills = chosen
	local out = { auras = { }, curses = { }, auraEffect = spec.auraEffect, life = spec.life, level = spec.level }
	local levels = spec.levels or { }
	for _, name in ipairs(chosen) do
		local effect = Roster.skillEffects[name]
		local gem = Roster.skillGems[name]
		local entry = { name = gem and gem.gem or name, supports = gem and gem.supports, level = levels[name] or 20, quality = 0, skill = name }
		-- Mercenary-exclusive supports on this skill
		for _, support in ipairs((spec.supports or { })[name] or { }) do
			local def = Roster.supports[support]
			if def then
				entry.curseEffect = (entry.curseEffect or 0) + (def.curseEffect or 0)
			else
				table.insert(report.unmodelled, string.format("%s support on %s", support, name))
			end
		end
		if effect == "aura" or (effect == "vaalaura" and spec.includeVaal) then
			table.insert(out.auras, entry)
			table.insert(report.estimated, name)
		elseif effect == "curse" or effect == "mark" then
			table.insert(out.curses, entry)
			table.insert(report.estimated, name)
		elseif effect == "ally" or effect == "vaalaura" then
			table.insert(report.unmodelled, name)
		end
	end
	return out, report
end

local function key(spec)
	local parts = { tostring(spec.level or 90) }
	for _, group in ipairs({ spec.auras or { }, spec.curses or { } }) do
		for _, s in ipairs(group) do
			table.insert(parts, string.format("%s/%s/%s/%s", s.name, s.level or 20, s.quality or 0, table.concat(s.supports or { }, "+")))
		end
		table.insert(parts, "|")
	end
	return table.concat(parts, ",")
end

---Calculate the mercenary's buffs in a throw-away build. Replaces the global build: load the
---player build afterwards. Results are cached per explicit spec.
---@return table { aura = text, curse = text }
function M.export(spec)
	local k = key(spec)
	if cache[k] then
		return cache[k]
	end
	local groups, grants, names = { }, { }, { }
	for _, s in ipairs(spec.auras or { }) do table.insert(names, s) end
	for _, s in ipairs(spec.curses or { }) do table.insert(names, s) end
	for _, s in ipairs(names) do
		local kind, name = classify(s.name)
		if kind == "gem" then
			local gems = { string.format('<Gem nameSpec="%s" level="%d" quality="%d" enabled="true"/>', xmlEscape(name), s.level or 20, s.quality or 0) }
			for _, support in ipairs(s.supports or { }) do
				table.insert(gems, string.format('<Gem nameSpec="%s" level="20" quality="0" enabled="true"/>', xmlEscape(support)))
			end
			table.insert(groups, '<Skill enabled="true" mainActiveSkill="1" label="mercenary">' .. table.concat(gems) .. '</Skill>')
		else
			table.insert(grants, string.format("Grants Level %d %s", s.level or 20, name))
		end
	end
	local xml = table.concat({
		'<?xml version="1.0" encoding="UTF-8"?><PathOfBuilding>',
		string.format('<Build level="%d" targetVersion="3_0" className="Scion" ascendClassName="None" mainSocketGroup="1" viewMode="CONFIG"/>', spec.level or 90),
		'<Skills activeSkillSet="1"><SkillSet id="1">', table.concat(groups), '</SkillSet></Skills>',
		'<Tree activeSpec="1"><Spec treeVersion="', latestTreeVersion, '" classId="0" ascendClassId="0" nodes=""/></Tree>',
		'<Items/><Config/></PathOfBuilding>',
	})
	loadBuildFromXML(xml, "mercenary")
	-- Skills the mercenary has without a gem (e.g. Envy) come from an item that grants them
	if #grants > 0 then
		local item = new("Item"):Item("Rarity: RARE\nMercenary Skills\nOnyx Amulet\nImplicits: 0\n" .. table.concat(grants, "\n"))
		build.itemsTab:AddItem(item, true)
		build.itemsTab.slots["Amulet"]:SetSelItemId(item.id)
		build.itemsTab:PopulateSlots()
	end
	build.partyTab.enableExportBuffs = true
	build.buildFlag = true
	runCallback("OnFrame")
	local result = { aura = build.partyTab:exportBuffs("Aura"), curse = build.partyTab:exportBuffs("Curse") }
	build.partyTab.enableExportBuffs = false
	cache[k] = result
	return result
end

---Add increased effect to buffs in a Party text (the effect line follows each buff name).
---@param increase number|function % for every buff, or function(name) returning the % for that buff
---@param curse boolean Curse text: a curse limit header, and an isMark line after the effect
function M.addEffect(text, increase, curse)
	if not increase or increase == 0 then
		return text
	end
	local out, expect, name = { }, curse and "limitHeader" or "name", nil
	for line in (text .. "\n"):gmatch("([^\n]*)\n") do
		if expect == "limitHeader" then
			expect = line:match("^%-%-%- Curse Limit") and "limit" or "name"
		elseif expect == "limit" then
			expect = "name"
		elseif expect == "effect" and tonumber(line) then
			local add
			if type(increase) == "function" then add = increase(name) else add = increase end
			line = tostring(tonumber(line) + (add or 0))
			expect = "mods"
		elseif expect == "name" and line ~= "" and line ~= "extraAura" and line ~= "otherEffects" then
			name = line
			expect = "effect"
		elseif line == "---" then
			expect = "name"
		end
		table.insert(out, line)
	end
	return (table.concat(out, "\n"):gsub("\n$", ""))
end
M.addAuraEffect = function(text, increase) return M.addEffect(text, increase, false) end

-- Increased effect of the mercenary's Non-Curse Auras granted by the player's passives
local function playerAuraEffectOnMercenary()
	local total, sources = 0, { }
	for _, node in pairs(build.spec.allocNodes) do
		for _, line in ipairs(node.sd or { }) do
			local num = line:lower():match("your mercenary has (%d+)%% increased effect of non%-curse auras from skills")
			if num then
				total = total + tonumber(num)
				table.insert(sources, node.dn)
			end
		end
	end
	return total, sources
end

---Put the mercenary into the loaded player build: Party tab auras and curses, Config Life.
---@param spec table explicit spec (after M.resolve)
---@return table description of what was applied
function M.apply(spec, exported, report)
	report = report or { }
	local fromPassives, sources = playerAuraEffectOnMercenary()
	local increase = fromPassives + (spec.auraEffect or 0)
	local auraText = M.addEffect(exported.aura or "", increase, false)
	local curseEffect = { }
	for _, s in ipairs(spec.curses or { }) do
		if s.curseEffect then curseEffect[s.name] = s.curseEffect end
	end
	local curseText = M.addEffect(exported.curse or "", function(name) return curseEffect[name] end, true)
	local party = build.partyTab
	party.controls.editAuras:SetText(auraText)
	party.controls.editCurses:SetText(curseText)
	party.actor = { Aura = { }, Curse = { }, Warcry = { }, Link = { }, modDB = new("ModDB"):ModDB(), output = { } }
	party.actor.modDB.actor = party.actor
	party.enemyModList = new("ModList"):ModList()
	local controls = { PartyMemberStats = "editPartyMemberStats", Aura = "editAuras", Curse = "editCurses", Warcry = "editWarcries", Link = "editLinks" }
	local labels = { Aura = "simpleAuras", Curse = "simpleCurses", Warcry = "simpleWarcries", Link = "simpleLinks" }
	for _, kind in ipairs({ "PartyMemberStats", "Aura", "Curse", "Warcry", "Link" }) do
		local target = kind == "PartyMemberStats" and party.actor.modDB or party.actor[kind]
		local label = kind == "PartyMemberStats" and party.actor.output or party.controls[labels[kind]]
		party:ParseBuffs(target, party.controls[controls[kind]].buf, kind, label)
	end
	party:ParseBuffs(party.enemyModList, party.controls.enemyCond.buf, "EnemyConditions")
	party:ParseBuffs(party.enemyModList, party.controls.enemyMods.buf, "EnemyMods", party.controls.simpleEnemyMods)
	if spec.life then
		build.configTab.input.TotalMercenaryLife = spec.life
		build.configTab:BuildModList()
	end
	build.buildFlag = true
	local auras, curses = { }, { }
	for _, s in ipairs(spec.auras or { }) do table.insert(auras, s.skill or s.name) end
	for _, s in ipairs(spec.curses or { }) do table.insert(curses, s.skill or s.name) end
	local assumptions = { "auras reach you and your main minion; curses share the enemy's curse slots with yours and your minions'" }
	if #auras + #curses > 0 then
		table.insert(assumptions, "mercenary skills are calculated from the gem versions (level 20, quality 0 unless set); the real mercenary values may differ")
	end
	if #curses > 0 then
		table.insert(assumptions, "mercenaries avoid cursing enemies that are already cursed; with curses of your own the mercenary's curse may not be used")
	end
	return {
		class = report.class,
		skills = report.skills,
		auras = auras,
		curses = curses,
		auraEffectIncrease = increase,
		auraEffectSources = sources,
		curseEffectIncrease = next(curseEffect) and curseEffect or nil,
		life = spec.life,
		notCalculated = #(report.unmodelled or { }) > 0 and report.unmodelled or nil,
		warnings = #(report.warnings or { }) > 0 and report.warnings or nil,
		assumptions = assumptions,
	}
end

---Roster for the AI: one class in full, or a short line per class.
function M.describe(name)
	local function effects(list)
		local out = { }
		for _, skill in ipairs(list) do
			table.insert(out, { name = skill, effect = Roster.skillEffects[skill] or "self" })
		end
		return out
	end
	local list = { }
	for _, c in ipairs(Roster.classes) do
		if not name or c.name:lower() == name:lower() or c.attributes:lower() == name:lower() or c.house:lower() == name:lower() then
			table.insert(list, { name = c.name, house = c.house, attributes = c.attributes, weapons = c.weapons, infamous = c.infamous, note = c.note,
				primary = effects(c.primary),
				secondary = { pick = c.secondary.pick, options = effects(c.secondary.options) },
				utility = { pick = c.utility.pick, options = effects(c.utility.options) } })
		end
	end
	return list
end

return M
