-- Path of Building
--
-- Luminary mercenary model. PoB has no mercenary; its Party tab already handles an ally's auras
-- (with their effect, on you and your minions) and curses (sharing the enemy's curse slots with
-- yours and your minions'). The mercenary is modelled as that party member:
--
--   1. its skills are calculated in a throw-away PoB build with the gems the mercenary uses, whose
--      Party export gives the aura and curse buffs in PoB's own text format;
--   2. the player's own "increased effect of Non-Curse Auras" on the mercenary (Bestowed Knighthood)
--      is added to the aura effect;
--   3. the text goes into the player build's Party tab, so it is also saved with the build and
--      visible in the PoB GUI;
--   4. the mercenary's Life goes into Config (TotalMercenaryLife) for Loyal Bodyguard.
--
-- spec = {
--   auras  = { { name = "Zealotry", level = 20, quality = 20 }, ... },  -- gem names or granted skills (e.g. Envy)
--   curses = { { name = "Despair", level = 20, quality = 20 } },
--   auraEffect = 0,     -- extra increased aura effect the mercenary has itself (gear), in %
--   life = 8000,        -- mercenary maximum Life (from the game), for Loyal Bodyguard
--   level = 90,         -- mercenary level (gem level requirements are not checked)
-- }

local M = { }

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
	error("unknown mercenary skill '" .. tostring(name) .. "'")
end

local function key(spec)
	local parts = { tostring(spec.level or 90) }
	for _, group in ipairs({ spec.auras or { }, spec.curses or { } }) do
		for _, s in ipairs(group) do
			table.insert(parts, string.format("%s/%s/%s", s.name, s.level or 20, s.quality or 0))
		end
		table.insert(parts, "|")
	end
	return table.concat(parts, ",")
end

---Calculate the mercenary's buffs in a throw-away build. Replaces the global build: load the
---player build afterwards. Results are cached per spec.
---@return table { aura = text, curse = text, skills = { names } }
function M.export(spec)
	local k = key(spec)
	if cache[k] then
		return cache[k]
	end
	local gems, grants, names = { }, { }, { }
	for _, s in ipairs(spec.auras or { }) do table.insert(names, s) end
	for _, s in ipairs(spec.curses or { }) do table.insert(names, s) end
	for _, s in ipairs(names) do
		local kind, name = classify(s.name)
		if kind == "gem" then
			table.insert(gems, string.format('<Skill enabled="true" mainActiveSkill="1" label="mercenary"><Gem nameSpec="%s" level="%d" quality="%d" enabled="true"/></Skill>',
				xmlEscape(name), s.level or 20, s.quality or 0))
		else
			table.insert(grants, string.format("Grants Level %d %s", s.level or 20, name))
		end
	end
	local xml = table.concat({
		'<?xml version="1.0" encoding="UTF-8"?><PathOfBuilding>',
		string.format('<Build level="%d" targetVersion="3_0" className="Scion" ascendClassName="None" mainSocketGroup="1" viewMode="CONFIG"/>', spec.level or 90),
		'<Skills activeSkillSet="1"><SkillSet id="1">', table.concat(gems), '</SkillSet></Skills>',
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

---Add increased aura effect to every aura in a Party "Aura" text (effect line after each name).
function M.addAuraEffect(text, increase)
	if not increase or increase == 0 then
		return text
	end
	local out, expect = { }, "name"
	for line in (text .. "\n"):gmatch("([^\n]*)\n") do
		if expect == "effect" and tonumber(line) then
			line = tostring(tonumber(line) + increase)
			expect = "mods"
		elseif expect == "name" and line ~= "" and line ~= "extraAura" and line ~= "otherEffects" then
			expect = "effect"
		elseif line == "---" then
			expect = "name"
		end
		table.insert(out, line)
	end
	return table.concat(out, "\n"):gsub("\n$", "")
end

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
---@return table description of what was applied
function M.apply(spec, exported)
	local fromPassives, sources = playerAuraEffectOnMercenary()
	local increase = fromPassives + (spec.auraEffect or 0)
	local auraText = M.addAuraEffect(exported.aura or "", increase)
	local party = build.partyTab
	party.controls.editAuras:SetText(auraText)
	party.controls.editCurses:SetText(exported.curse or "")
	party.actor = { Aura = { }, Curse = { }, Warcry = { }, Link = { }, modDB = new("ModDB"):ModDB(), output = { } }
	party.actor.modDB.actor = party.actor
	party.enemyModList = new("ModList"):ModList()
	for _, kind in ipairs({ "PartyMemberStats", "Aura", "Curse", "Warcry", "Link" }) do
		local control = ({ PartyMemberStats = "editPartyMemberStats", Aura = "editAuras", Curse = "editCurses", Warcry = "editWarcries", Link = "editLinks" })[kind]
		local target = kind == "PartyMemberStats" and party.actor.modDB or party.actor[kind]
		local label = kind == "PartyMemberStats" and party.actor.output or party.controls[({ Aura = "simpleAuras", Curse = "simpleCurses", Warcry = "simpleWarcries", Link = "simpleLinks" })[kind]]
		party:ParseBuffs(target, party.controls[control].buf, kind, label)
	end
	party:ParseBuffs(party.enemyModList, party.controls.enemyCond.buf, "EnemyConditions")
	party:ParseBuffs(party.enemyModList, party.controls.enemyMods.buf, "EnemyMods", party.controls.simpleEnemyMods)
	if spec.life then
		build.configTab.input.TotalMercenaryLife = spec.life
		build.configTab:BuildModList()
	end
	build.buildFlag = true
	local names = { }
	for _, s in ipairs(spec.auras or { }) do table.insert(names, s.name) end
	return {
		auras = names,
		curses = (function() local c = { } for _, s in ipairs(spec.curses or { }) do table.insert(c, s.name) end return c end)(),
		auraEffectIncrease = increase,
		auraEffectSources = sources,
		life = spec.life,
		note = "auras affect you and your main minion; curses share the enemy's curse slots with yours and your minions'",
	}
end

return M
