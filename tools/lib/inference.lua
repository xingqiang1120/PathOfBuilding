-- Path of Building
--
-- Condition inference: estimate Config values that PoB leaves to the user (default 0) from what
-- the build actually does. First case: withered stacks.
--
-- Withered (PoE Wiki, "Withered"): 6% increased chaos damage taken per stack, up to 15 stacks; each
-- stack has its own duration (2 s base) and is not refreshed by new stacks. Unholy Might gives a
-- 25% chance to inflict Withered on hit (PoE Wiki, "Unholy Might").
--
-- Steady state: stacks = min(15, hits per second x chance x duration), summed over everything that
-- hits the target (the player and, for minion skills, every minion alive).
--
-- PoB parses "X% chance to inflict Withered" lines only to a "can wither" flag and drops the
-- chance, so the chances are read from the modifier text here.

local M = { }

-- Rule values come from the mechanics knowledge base (src/Data/Mechanics.lua), the single source of truth
local function rule(mechanicId, key)
	local mech = autoTags.GetMechanic(mechanicId)
	local entry = assert(mech and mech.rules and mech.rules[key], "missing mechanic rule " .. mechanicId .. "." .. key)
	return entry.value
end
M.WITHER_MAX = rule("withered", "maxStacks")
M.WITHER_BASE_DURATION = rule("withered", "baseDurationSeconds")
M.UNHOLY_MIGHT_WITHER_CHANCE = rule("unholymight", "witherChanceOnHitPercent")

-- Text sources: pattern, who hits, which capture is the chance (nil = always), duration capture
local witherPatterns = {
	{ pattern = "^minions have (%d+)%% chance to inflict withered on hit", actor = "minion", chance = 1 },
	{ pattern = "^(%d+)%% chance to inflict withered for (%d+) seconds on hit", actor = "player", chance = 1, duration = 2 },
	{ pattern = "^(%d+)%% chance to inflict withered for two seconds on hit", actor = "player", chance = 1 },
	{ pattern = "^inflict withered for (%d+) seconds on hit", actor = "player", duration = 1 },
}

local function round(v, n)
	local m = 10 ^ (n or 2)
	return math.floor(v * m + 0.5) / m
end

-- Every modifier line the build uses: equipped items (current variants) and allocated passives
local function buildLines(build)
	local lines = { }
	local itemsTab = build.itemsTab
	for _, slot in ipairs(itemsTab.orderedSlots or { }) do
		local item = slot.selItemId and itemsTab.items[slot.selItemId]
		if item and slot:IsShown() ~= false then
			for _, group in ipairs({ "enchantModLines", "implicitModLines", "explicitModLines", "crucibleModLines" }) do
				for _, ml in ipairs(item[group] or { }) do
					if item:CheckModLineVariant(ml) then
						-- Resolve "(20-25)%" style ranges to the item's rolled value
						local text = ml.range and itemLib.applyRange(ml.line, ml.range, ml.valueScalar) or ml.line
						table.insert(lines, { text = text, source = item.title or item.name })
					end
				end
			end
		end
	end
	for _, node in pairs(build.spec.allocNodes) do
		for _, line in ipairs(node.sd or { }) do
			table.insert(lines, { text = line, source = node.dn })
		end
	end
	return lines
end

local function combineChance(list)
	local miss = 1
	for _, c in ipairs(list) do
		miss = miss * (1 - math.min(c, 100) / 100)
	end
	return (1 - miss) * 100
end

---Estimate withered stacks for the current main skill.
---@param build table
---@param opts table? { minionCount = number }
---@return table|nil inference
function M.inferWithered(build, opts)
	opts = opts or { }
	local env = build.calcsTab.mainEnv
	local out = build.calcsTab.mainOutput
	local actors = { player = { chances = { }, sources = { }, duration = M.WITHER_BASE_DURATION },
		minion = { chances = { }, sources = { }, duration = M.WITHER_BASE_DURATION } }

	-- Unholy Might, wherever PoB says the actor has it
	if env.player.modDB:Flag(nil, "UnholyMight") then
		table.insert(actors.player.chances, M.UNHOLY_MIGHT_WITHER_CHANCE)
		table.insert(actors.player.sources, "Unholy Might (25%)")
	end
	if env.minion and env.minion.modDB:Flag(nil, "UnholyMight") then
		table.insert(actors.minion.chances, M.UNHOLY_MIGHT_WITHER_CHANCE)
		table.insert(actors.minion.sources, "minions' Unholy Might (25%)")
	end
	-- Support gems that grant a wither chance (e.g. Withering Touch), only when they support the skill used
	local function addSupportChances(skill, actor)
		for _, effect in ipairs(skill and skill.effectList or { }) do
			for _, stat in ipairs(effect.grantedEffect.constantStats or { }) do
				if stat[1] == "withered_on_hit_chance_%" and effect.grantedEffect.support then
					table.insert(actor.chances, stat[2])
					table.insert(actor.sources, string.format("%s support (%d%%)", effect.grantedEffect.name, stat[2]))
				end
			end
		end
	end
	addSupportChances(env.player.mainSkill, actors.player)
	if env.minion then
		addSupportChances(env.minion.mainSkill, actors.minion)
	end
	-- Explicit chances from modifier text
	for _, line in ipairs(buildLines(build)) do
		local text = line.text:lower()
		for _, rule in ipairs(witherPatterns) do
			local caps = { text:match(rule.pattern) }
			if caps[1] then
				local chance = rule.chance and tonumber(caps[rule.chance]) or 100
				local actor = actors[rule.actor]
				table.insert(actor.chances, chance)
				table.insert(actor.sources, string.format("%s: %s", line.source, line.text))
				if rule.duration and tonumber(caps[rule.duration]) then
					actor.duration = math.max(actor.duration, tonumber(caps[rule.duration]))
				end
				break
			end
		end
	end

	local parts, total, assumptions = { }, 0, { }
	-- Player hits (only when the main skill is the player's own)
	if #actors.player.chances > 0 and not env.minion and (out.Speed or 0) > 0 then
		local hitsPerSecond = out.Speed * (out.HitChance or 100) / 100
		local chance = combineChance(actors.player.chances)
		local stacks = hitsPerSecond * chance / 100 * actors.player.duration
		total = total + stacks
		table.insert(parts, { actor = "player", hitsPerSecond = round(hitsPerSecond), chance = round(chance, 1),
			duration = actors.player.duration, stacks = round(stacks), sources = actors.player.sources })
	end
	-- Minion hits
	if #actors.minion.chances > 0 and env.minion and out.Minion and (out.Minion.Speed or 0) > 0 then
		local limit = out.ActiveMinionLimit or 1
		local count = opts.minionCount or limit
		local hitsPerSecond = out.Minion.Speed * (out.Minion.HitChance or 100) / 100
		local chance = combineChance(actors.minion.chances)
		local stacks = count * hitsPerSecond * chance / 100 * actors.minion.duration
		total = total + stacks
		table.insert(parts, { actor = "minion", minions = count, minionLimit = limit, hitsPerSecondEach = round(hitsPerSecond),
			chance = round(chance, 1), duration = actors.minion.duration, stacks = round(stacks), sources = actors.minion.sources })
		if not opts.minionCount then
			table.insert(assumptions, string.format("all %d minions alive and hitting the same target (steady state, not the start of a fight)", limit))
		end
	end
	if #parts == 0 then
		return nil
	end
	table.insert(assumptions, "each hit can apply one stack; extra projectiles hitting the same target and withered duration modifiers are not counted")
	local value = math.min(M.WITHER_MAX, math.floor(total))
	local needed
	for _, part in ipairs(parts) do
		if part.actor == "minion" and part.stacks > 0 then
			needed = math.ceil(M.WITHER_MAX / (part.stacks / part.minions))
		end
	end
	return {
		key = "multiplierWitheredStackCount",
		label = "Withered stacks on the enemy",
		value = value,
		estimate = round(total),
		parts = parts,
		minionsNeededForMax = needed,
		assumptions = assumptions,
		formula = "min(15, hits per second x chance x duration), summed over the player and every minion",
		mechanics = { "withered", "unholymight" },
	}
end

---Feeding Frenzy: minions from skills supported by Feeding Frenzy Support grant the buff on hit with a
---chance per hit; the buff lasts a few seconds. Uptime with Poisson-distributed hits:
---uptime = 1 - exp(-(hits per second x chance) x duration). Considered permanent at 90% or more.
function M.inferFeedingFrenzy(build, opts)
	opts = opts or { }
	local env = build.calcsTab.mainEnv
	local out = build.calcsTab.mainOutput
	local skill = env.player.mainSkill
	if not (env.minion and out.Minion and skill) then
		return nil
	end
	local support
	for _, effect in ipairs(skill.effectList or { }) do
		if effect.grantedEffect.support and effect.grantedEffect.name == "Feeding Frenzy" then
			support = effect
		end
	end
	if not support then
		return nil
	end
	local levelData = support.grantedEffect.levels[support.level] or support.grantedEffect.levels[1]
	local chance, durationMs = levelData[1], levelData[2]
	local count = opts.minionCount or out.ActiveMinionLimit or 1
	local hitsPerSecond = count * (out.Minion.Speed or 0) * (out.Minion.HitChance or 100) / 100
	local uptime = 1 - math.exp(-hitsPerSecond * chance / 100 * durationMs / 1000)
	local assumptions = { "buff applications follow a Poisson process over all minions' hits" }
	if not opts.minionCount then
		table.insert(assumptions, 1, string.format("all %d minions alive and hitting (steady state)", count))
	end
	return {
		key = "feedingFrenzyFeedingFrenzyActive",
		label = "Feeding Frenzy active",
		value = uptime >= 0.9,
		estimate = round(uptime, 3),
		parts = { { actor = "minion", minions = count, hitsPerSecondEach = round((out.Minion.Speed or 0) * (out.Minion.HitChance or 100) / 100),
			chance = chance, duration = durationMs / 1000, sources = { string.format("Feeding Frenzy Support level %d (%d%%, %.1f s)", support.level, chance, durationMs / 1000) } } },
		assumptions = assumptions,
		formula = "uptime = 1 - exp(-hits per second x chance x duration); active when uptime >= 90%",
		mechanics = { "feedingfrenzy" },
	}
end

---All inferences for the current state of the build.
function M.infer(build, opts)
	local list = { }
	for _, fn in ipairs({ M.inferWithered, M.inferFeedingFrenzy }) do
		local inference = fn(build, opts)
		if inference then
			table.insert(list, inference)
		end
	end
	return list
end

return M
