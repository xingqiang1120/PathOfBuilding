-- Path of Building
--
-- Mechanics knowledge base
-- Game mechanics as data, shared by the tagger (Modules/AutoTags.lua), condition inference and AI tools.
-- Every rule value and fact names where it comes from, so it can be checked and corrected.
--
-- Fields
--   id, label, kind     kind: buff | debuff | minion | conversion | mechanic
--   summary             one or two sentences
--   implies             tag ids that always come with this mechanic (e.g. withered -> chaos)
--   detect              how items and passives are recognised (same matchers as Data/AutoTagRules.lua:
--                       modNames, modPatterns, textPatterns, textAlways). minionToo = also match inside
--                       "Minions have ..." modifiers. Omit detect when an existing tag already covers it
--                       (tag = existing tag id the knowledge attaches to).
--   rules               numbers used by calculations; each rule lists its source key
--   facts               statements with their source: { text, source, ref }
--                         source: "wiki" (PoE Wiki), "pobdata" (PoB game data export), "play" (confirmed in play)
--   refs                source pages
--
-- PoE Wiki content is CC BY-NC 3.0 (https://www.poewiki.net); keep the refs when copying facts.

local wiki = "https://www.poewiki.net/wiki/"

return {
	{
		id = "unholymight", label = "Unholy Might", kind = "buff",
		summary = "Converts 100% of physical damage to chaos damage and gives a 25% chance to inflict Withered on hit.",
		implies = { "chaos", "withered" },
		detect = {
			modNames = { ["Condition:UnholyMight"] = true },
			textPatterns = { "unholy might" },
			textAlways = true,
			minionToo = true,
		},
		rules = {
			physicalConvertedToChaosPercent = { value = 100, source = "wiki" },
			witherChanceOnHitPercent = { value = 25, source = "wiki" },
		},
		facts = {
			{ text = "Affected by increased buff effect; duration can be scaled indirectly through buff expiration rate.", source = "wiki", ref = wiki .. "Unholy_Might" },
			{ text = "Foulborn Vis Mortis and the Necromancer notable Unnatural Strength give minions permanent Unholy Might.", source = "wiki", ref = wiki .. "Unholy_Might" },
		},
		refs = { wiki .. "Unholy_Might" },
	},
	{
		id = "withered", label = "Withered", kind = "debuff",
		summary = "Each stack makes the target take 6% increased chaos damage, up to 15 stacks; every stack has its own 2 second duration.",
		implies = { "chaos" },
		detect = {
			modNames = { ["Condition:CanWither"] = true },
			modPatterns = { "^Multiplier:WitheredStack" },
			textPatterns = { "withered" },
			textAlways = true,
			minionToo = true,
		},
		rules = {
			maxStacks = { value = 15, source = "wiki" },
			chaosDamageTakenPerStackPercent = { value = 6, source = "wiki" },
			baseDurationSeconds = { value = 2, source = "wiki" },
			-- Increased effect of Withered only matters in steps of 1/6 (16.67%) per stack
			effectBreakpointPercent = { value = 16.67, source = "wiki" },
		},
		facts = {
			{ text = "New stacks do not refresh the duration of existing stacks.", source = "wiki", ref = wiki .. "Withered" },
			{ text = "Withering Touch Support grants a 25% chance to Wither on hit but only supports attack skills.", source = "pobdata", ref = wiki .. "Withering_Touch_Support" },
		},
		refs = { wiki .. "Withered" },
	},
	{
		id = "feedingfrenzy", label = "Feeding Frenzy", kind = "buff",
		summary = "Buff on the player granted by minions from skills supported by Feeding Frenzy Support: minions deal 10% more damage and have 10% increased attack, cast and movement speed.",
		implies = { "minion" },
		detect = {
			textPatterns = { "feeding frenzy" },
			textAlways = true,
		},
		rules = {
			moreMinionDamagePercent = { value = 10, source = "wiki" },
			increasedMinionSpeedPercent = { value = 10, source = "wiki" },
			grantChanceOnHitPercent = { min = 25, max = 44, source = "wiki", note = "by gem level 1-20" },
			baseDurationSeconds = { min = 4, max = 5.9, source = "wiki", note = "by gem level 1-20" },
		},
		facts = {
			{ text = "Supported minions are Aggressive; Aggressive and Defensive cancel each other out.", source = "wiki", ref = wiki .. "Feeding_Frenzy_Support" },
		},
		refs = { wiki .. "Feeding_Frenzy_Support" },
	},
	{
		id = "freshmeat", label = "Fresh Meat", kind = "buff",
		summary = "Buff on newly summoned minions from skills supported by Fresh Meat Support: added critical strike chance, critical strike multiplier and Adrenaline, for a share of the minion's own duration.",
		implies = { "minion", "crit" },
		detect = {
			textPatterns = { "fresh meat" },
			textAlways = true,
		},
		rules = {
			buffDurationPercentOfSummonDuration = { value = 10, source = "pobdata", note = "support_recent_minions_effect_duration_is_%_summon_duration" },
			maxBuffDurationSeconds = { value = 10, source = "pobdata", note = "support_recent_minions_max_effect_duration_ms" },
			addedCritChancePercent = { min = 2, max = 3.9, source = "pobdata", note = "by gem level 1-20" },
			addedCritMultiplierPercent = { min = 50, max = 69, source = "pobdata", note = "by gem level 1-20" },
		},
		facts = {
			{ text = "Each minion has the buff only for the first 10% of its duration (at most 10 s); PoB's Config 'Is Fresh Meat active?' applies it to every minion all the time.", source = "pobdata", ref = "src/Data/Skills/sup_int.lua" },
			{ text = "Minions with Fresh Meat also have Adrenaline, so the buff raises damage and speed as well as critical strikes.", source = "pobdata", ref = "src/Data/Skills/sup_int.lua" },
			{ text = "Share of minions with the buff = buff duration x summons per second / minions alive; fast re-summoning (e.g. corpses from Desecrate consumed by offerings with Soulwrest) keeps it high, and a lower minion limit makes full uptime easier.", source = "play", ref = "MeiMax-modify analysis 2026-11-19" },
		},
		refs = { wiki .. "Fresh_Meat_Support" },
	},
	{
		id = "phantasm", label = "Summoned Phantasm", kind = "minion",
		tag = "phantasm",
		summary = "Projectile spell-casting minion: a piercing physical projectile spell; summoned by Summon Phantasm Support, Soulwrest and similar sources.",
		implies = { "minion", "spell" },
		rules = {
			baseCastRate = { value = 0.85, source = "wiki" },
		},
		facts = {
			{ text = "Phantasms use a piercing physical projectile spell; their projectiles pierce all targets, so they cannot chain or fork.", source = "wiki", ref = wiki .. "Summon_Phantasm_Support" },
			{ text = "Summoning skills declare phantasm minion skill types as spell, projectile, physical, damage and duration - no attack - so attack-only supports such as Withering Touch do not support them.", source = "pobdata", ref = "src/Data/Skills/other.lua" },
			{ text = "Phantasms attack with Physical Projectile, not the melee Default Attack PoB used to select.", source = "play" },
			{ text = "The total number of phantasms is limited by the highest-level Summon Phantasm Support.", source = "wiki", ref = wiki .. "Summon_Phantasm_Support" },
			{ text = "The Dark Monarch: Maximum number of Summoned Phantasms is Doubled; cannot have minions other than Summoned Phantasms.", source = "pobdata", ref = "src/Data/Uniques/helmet.lua" },
		},
		refs = { wiki .. "Summon_Phantasm_Support" },
	},
}
