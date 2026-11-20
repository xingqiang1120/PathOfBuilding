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
--                         source: "wiki" (PoE Wiki), "pobdata" (PoB game data export or calculation code),
--                         "play" (confirmed in play), "pobcalc" (observed by running PoB's calculation on a build;
--                         ref names the build and analysis)
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
			{ text = "Soulwrest's phantasms: limit 11 from the staff, +10 from a Summon Phantasm Support linked to it, doubled by The Dark Monarch (42 vs 22). Replacing that support for per-minion damage halves the army; compare total damage (per minion x limit).", source = "pobcalc", ref = "MeiMax vs MeiMax-modify, 2026-11-19" },
		},
		refs = { wiki .. "Summon_Phantasm_Support" },
	},

	-- Defence layers (learned from the level 100 AWoRA Necromancer analysis, 2026-11-20)
	{
		id = "armour", label = "Armour", kind = "mechanic",
		tag = "armour",
		summary = "Reduces physical hit damage by armour / (armour + 5 x damage): strong against many small hits, weak against one big hit.",
		rules = {
			hitDamageFactor = { value = 5, source = "pobdata", note = "calcs.armourReductionF in src/Modules/CalcDefence.lua" },
			maxPhysicalDamageReductionPercent = { value = 90, source = "wiki" },
		},
		facts = {
			{ text = "Armour's reduction shrinks as the hit grows, so it does little for the maximum hit taken (one-shot threshold); flat additional physical damage reduction (endurance charges, Bone Barrier, Basalt Flask) applies in full to big hits and is the lever against one-shots, together with a larger life pool.", source = "pobdata", ref = "src/Modules/CalcDefence.lua" },
			{ text = "MeiMax (3,784 life, no flat reduction): Granite + Basalt flasks raise armour from 173 to 2,655 but the physical maximum hit only from 4,999 to 5,448 (+9%); adding 3 endurance charges brings it to 6,197.", source = "pobcalc", ref = "MeiMax defence simulation, 2026-11-20" },
		},
		refs = { wiki .. "Armour" },
	},
	{
		id = "endurancecharge", label = "Endurance Charges", kind = "buff",
		tag = "charges",
		summary = "Each endurance charge grants 4% additional physical damage reduction and 4% elemental damage reduction.",
		rules = {
			physicalReductionPerChargePercent = { value = 4, source = "pobdata", note = "physical_damage_reduction_%_per_endurance_charge, src/Data/Misc.lua" },
			elementalReductionPerChargePercent = { value = 4, source = "pobdata", note = "elemental_damage_reduction_%_per_endurance_charge, src/Data/Misc.lua" },
			baseMaxCharges = { value = 3, source = "pobdata", note = "max_endurance_charges, src/Data/Misc.lua" },
		},
		facts = {
			{ text = "PoB counts endurance charges only when Config 'Use Endurance Charges' is on, and then assumes the maximum; how the build generates them is not checked (e.g. Enduring Composure 'Gain 1 Endurance Charge every second if you've been Hit Recently' is not calculated).", source = "pobdata", ref = "src/Modules/CalcSetup.lua" },
			{ text = "AWoRA Necromancer: 5 charges are 20 of its 75% physical reduction; at the start of a fight without charges or flasks the physical maximum hit drops from 14,157 to 9,782 and the elemental one from 43,135 to 34,508.", source = "pobcalc", ref = "Animate Weapon of Ranged Arms (Necro, shared), 2026-11-20" },
		},
		refs = { wiki .. "Endurance_charge" },
	},
	{
		id = "block", label = "Block", kind = "mechanic",
		tag = "block",
		summary = "Chance to take no damage from a blocked hit; attack and spell block are capped at 75% unless the maximum is raised.",
		rules = {
			baseMaxBlockPercent = { value = 75, source = "pobdata", note = "BlockChanceMax / SpellBlockChanceMax Base" },
		},
		facts = {
			{ text = "Block protects against repeated hits; it does not raise the maximum hit taken, so a one-shot is decided by life and flat reduction, not by block.", source = "play", ref = "user's MeiMax experience (66/78 block, dies only to one-shots or rare streaks of unblocked hits)" },
			{ text = "Necromancer Mistress of Sacrifice makes offerings affect you at 50% effect: Bone Offering then gives about 38% attack and spell block to the player, which needs corpses (e.g. Desecrate) to keep up.", source = "pobcalc", ref = "Animate Weapon of Ranged Arms (Necro, shared), 2026-11-20" },
			{ text = "Rumi's Concoction adds attack and spell block and armour while active; on MeiMax it raises attack block from 66% to the 75% cap.", source = "pobcalc", ref = "MeiMax defence simulation, 2026-11-20" },
		},
		refs = { wiki .. "Block" },
	},
	{
		id = "flaskuptime", label = "Flask uptime", kind = "mechanic",
		tag = "flask",
		summary = "PoB applies a flask only when its slot is ticked active, and then as if it were always up.",
		facts = {
			{ text = "Flask effects are all-or-nothing in PoB (slot 'active'); real uptime depends on charges and flask duration, so defence that relies on flasks is overstated between flask uses.", source = "pobdata", ref = "src/Modules/CalcPerform.lua" },
			{ text = "AWoRA Necromancer: all five flasks active; with them off physical reduction drops from 75% to 50% and armour from 7,932 to 2,312.", source = "pobcalc", ref = "Animate Weapon of Ranged Arms (Necro, shared), 2026-11-20" },
		},
	},
	{
		id = "stonegolemsafeguarding", label = "Stone Golem of Safeguarding", kind = "minion",
		implies = { "minion" },
		detect = {
			textPatterns = { "stone golem" },
			textAlways = true,
		},
		summary = "Golem that takes part of the melee hit damage you receive from its own life before yours, and can taunt enemies.",
		rules = {
			meleeDamageTakenByGolemPercent = { value = 15, source = "pobdata", note = "stone_golem_grants_melee_damage_removed_from_stone_golem_before_life_or_es_%" },
		},
		facts = {
			{ text = "PoB models the redirect as a melee-only life pool in effective HP (takenFromStoneGolemBeforeYou); the golem's taunt is not modelled.", source = "pobdata", ref = "src/Modules/CalcDefence.lua" },
			{ text = "Increased effect of the buff granted by Stone Golems (e.g. Soul Span) scales the golem's buff.", source = "pobdata", ref = "src/Modules/ModParser.lua" },
		},
	},
	{
		id = "minionleech", label = "Life leech from minion damage", kind = "mechanic",
		implies = { "minion", "life" },
		detect = {
			textPatterns = { "damage dealt by your minions is leeched" },
			textAlways = true,
		},
		summary = "Leeching life from the damage your minions deal (e.g. Necromancer Bone Barrier: 1%).",
		facts = {
			{ text = "PoB does not calculate 'X% of Damage Dealt by your Minions is Leeched to you as Life'; with high minion damage it can be the main recovery, so recovery is understated.", source = "pobdata", ref = "reports/coverage (life_leech_from_minion_damage_%)" },
		},
	},
	{
		id = "mercenary", label = "Mercenary (Luminary)", kind = "minion",
		implies = { "minion" },
		detect = {
			textPatterns = { "mercenar" },
			textAlways = true,
		},
		summary = "Luminary's mercenary fights beside you. Modelled as a Party member (tools/lib/mercenary.lua): its auras and curses, and Loyal Bodyguard from its Life.",
		rules = {
			bestowedKnighthoodAuraEffectPercent = { value = 50, source = "pobdata", note = "Bestowed Knighthood: Your Mercenary has 50% increased effect of Non-Curse Auras from Skills" },
			loyalBodyguardHitDamageTakenPercent = { value = 20, source = "pobdata", note = "Loyal Bodyguard, only while the mercenary's Life is higher than yours" },
		},
		facts = {
			{ text = "The mercenary taunts enemies (Bestowed Knighthood), so the player is hit much less often; hit frequency is not part of PoB's numbers.", source = "play", ref = "user's MeiMax experience" },
			{ text = "The mercenary's auras reach you and your minions at 150% effect with Bestowed Knighthood; in PoB they go through the Party tab (calculated from the mercenary's gems), which is saved with the build.", source = "pobdata", ref = "tools/lib/mercenary.lua, src/Modules/CalcPerform.lua" },
			{ text = "Curses count against one shared limit for the player, the mercenary and minions; in PoB the mercenary's curse takes a free curse slot only, the player's own curses keep theirs.", source = "play", ref = "user, 2026-11-20; src/Modules/CalcPerform.lua curse slots" },
			{ text = "Loyal Bodyguard: 20% of hit damage is taken from the mercenary's Life while it is higher than yours; set the mercenary's Life in Config ('Mercenary maximum Life'). The 40% recoup when its Life is lower is not modelled.", source = "pobdata", ref = "src/Modules/CalcDefence.lua" },
			{ text = "MeiMax with a mercenary using Zealotry 20/20, Envy 25 and Despair 20/20 and 8,000 Life: per-phantasm DPS 37,584 -> 88,168 (Despair alone -> 55,303, auras alone -> 59,920); physical maximum hit 4,999 -> 6,240.", source = "pobcalc", ref = "MeiMax, assumed mercenary gems, 2026-11-20" },
			{ text = "Not modelled: the mercenary's own damage, its unique items (Legendary nodes), Link skill buffs on it (Golden Glory).", source = "pobdata", ref = "Luminary ascendancy lines unsupported in ModParser" },
		},
	},
}
