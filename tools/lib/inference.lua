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

M.buildLines = buildLines

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

---Fresh Meat share of minions buffed. Pure function so it can be tested without a build.
---Minions alive = min(limit, summons per second x minion duration); buffed = min(alive, summons per second x buff duration).
---@param rate number summons per second
---@param limit number minion limit
---@param minionDuration number|nil seconds (nil = minions do not expire)
---@param buffDuration number seconds
function M.freshMeatUptime(rate, limit, minionDuration, buffDuration)
	if rate <= 0 or limit <= 0 then
		return 0, 0, 0
	end
	local alive = minionDuration and math.min(limit, rate * minionDuration) or limit
	local buffed = math.min(alive, rate * buffDuration)
	return buffed / alive, alive, buffed
end

---Fresh Meat: each minion has the buff only for the first share of its own duration, so the share of the army with
---the buff depends on how fast minions are re-summoned. The summon rate is not in the build; it comes from play
---(opts.summonRate, minions per second). Without it the inference only reports the rate needed for full uptime.
function M.inferFreshMeat(build, opts)
	opts = opts or { }
	local env = build.calcsTab.mainEnv
	local out = build.calcsTab.mainOutput
	local skill = env.player.mainSkill
	if not (env.minion and out.Minion and skill) then
		return nil
	end
	local support
	for _, effect in ipairs(skill.effectList or { }) do
		if effect.grantedEffect.support and effect.grantedEffect.name == "Fresh Meat" then
			support = effect
		end
	end
	if not support then
		return nil
	end
	local share, maxMs = 10, 10000
	for _, stat in ipairs(support.grantedEffect.constantStats or { }) do
		if stat[1] == "support_recent_minions_effect_duration_is_%_summon_duration" then share = stat[2] end
		if stat[1] == "support_recent_minions_max_effect_duration_ms" then maxMs = stat[2] end
	end
	local minionDuration = (out.Duration or 0) > 0 and out.Duration or nil
	local buffDuration = math.min(maxMs / 1000, (minionDuration or math.huge) * share / 100)
	local limit = out.ActiveMinionLimit or 1
	local fullRate = limit / buffDuration
	local result = {
		key = "freshMeatBuffs",
		label = "Fresh Meat active (share of minions with the buff)",
		blend = true,
		requiredRateForFull = round(fullRate, 2),
		formula = "share = min(alive, summons/s x buff duration) / alive; alive = min(limit, summons/s x minion duration); buff duration = min(10 s, 10% of minion duration)",
		mechanics = { "freshmeat" },
	}
	local part = { actor = "minion", minionLimit = limit, minionDuration = minionDuration and round(minionDuration),
		buffDuration = round(buffDuration), sources = { string.format("Fresh Meat Support level %d (%d%% of minion duration, max %.0f s)", support.level, share, maxMs / 1000) } }
	result.parts = { part }
	if not opts.summonRate then
		result.value = nil
		result.needs = "summonRate"
		result.assumptions = { string.format("summon rate unknown: full uptime needs %.1f summons per second with %d minions; pass summonRate (from play) to estimate", fullRate, limit) }
		return result
	end
	local uptime, alive, buffed = M.freshMeatUptime(opts.summonRate, limit, minionDuration, buffDuration)
	part.summonRate, part.alive, part.buffed = opts.summonRate, round(alive, 1), round(buffed, 1)
	result.value = uptime > 0
	result.estimate = round(uptime, 3)
	result.uptime = uptime
	result.override = true -- a summon rate from play is more specific than the build's on/off Config switch
	result.assumptions = {
		string.format("%.2f summons per second (from play), sustained", opts.summonRate),
		"at the minion limit a new summon replaces the oldest minion",
		"minion DPS is blended: share x DPS with the buff + (1 - share) x DPS without it",
		"minions are not killed before their duration ends",
	}
	return result
end

---Skill stages that come from something else in the build. With no stage count set, PoB counts the maximum stages,
---which is right for stages the skill builds itself (channelling, Blade Flurry, Incinerate), but not for stages that
---need another skill or a fuse rate:
--- * Blade Blast detonates Lingering Blades (left by Bladefall / Ethereal Knives of Lingering Blades); none -> only its own hit.
--- * Blade Blast of Unloading detonates the player's Blade Vortex blades; no Blade Vortex -> only its own hit.
--- * Explosive Arrow: fuses on one enemy = arrows that land within the fuse duration (attack rate x hit chance x duration).
---Returns a stage inference (kind "stages"); the worker applies it to the main skill's gem.
local function hasGem(build, pattern)
	for _, group in ipairs(build.skillsTab.socketGroupList or { }) do
		if group.enabled ~= false then
			for _, gem in ipairs(group.gemList or { }) do
				local name = gem.grantedEffect and gem.grantedEffect.name or gem.nameSpec or ""
				if gem.enabled ~= false and name:match(pattern) then
					return name
				end
			end
		end
	end
end
M.hasGem = hasGem

local stageRules = {
	["Blade Blast"] = function(build, out, max)
		local source = hasGem(build, "^Bladefall") or hasGem(build, "^Ethereal Knives of Lingering Blades")
		if source then
			return nil, { string.format("Lingering Blades from %s: the number on the ground depends on play (PoB counts %d)", source, max) }
		end
		return 1, { "no skill in the build leaves Lingering Blades (Bladefall, Ethereal Knives of Lingering Blades): Blade Blast only hits once" }
	end,
	["Blade Blast of Unloading"] = function(build, out, max)
		local source = hasGem(build, "^Blade Vortex")
		if source then
			return nil, { string.format("detonates the blades of %s (PoB counts %d)", source, max) }
		end
		return 1, { "no Blade Vortex in the build: no blades to detonate, only its own hit" }
	end,
	["Explosive Arrow"] = function(build, out, max)
		local rate, duration = (out.Speed or 0) * (out.HitChance or 100) / 100, out.Duration or 0
		if rate <= 0 or duration <= 0 then
			return nil, { "attack rate or fuse duration unknown" }
		end
		local fuses = math.max(1, math.min(max, math.floor(rate * duration)))
		return fuses, { string.format("%.2f arrows per second x %.2f s fuse duration on one enemy (more projectiles hitting the same enemy are not counted)", rate, duration) }
	end,
}

function M.inferStages(build, opts)
	local skill = build.calcsTab.mainEnv.player.mainSkill
	local effect = skill and skill.activeEffect
	local name = effect and effect.grantedEffect and effect.grantedEffect.name
	local rule = name and stageRules[name]
	local max = skill and skill.skillData and skill.skillData.stagesMax
	if not (rule and max) then
		return nil
	end
	local value, assumptions = rule(build, build.calcsTab.mainOutput, max)
	return {
		kind = "stages",
		key = "skillStageCount",
		skill = name,
		label = name .. " stages",
		value = value,
		estimate = value,
		maximum = max,
		needs = value == nil and "the stage count from play" or nil,
		assumptions = assumptions,
		formula = "PoB counts the maximum stages when none is set; stages fed by another skill or by attack rate are estimated",
	}
end

---All inferences for the current state of the build.
function M.infer(build, opts)
	local list = { }
	for _, fn in ipairs({ M.inferWithered, M.inferFeedingFrenzy, M.inferFreshMeat, M.inferStages }) do
		local inference = fn(build, opts)
		if inference then
			table.insert(list, inference)
		end
	end
	return list
end

return M
