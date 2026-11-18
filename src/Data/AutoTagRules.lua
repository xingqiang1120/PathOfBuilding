-- Path of Building
--
-- Auto tag rules
-- Data-driven rules that derive build-archetype tags from parsed modifiers.
-- Used by Modules/AutoTags.lua to classify items and passive nodes.
--
-- Each rule may use any of the following matchers (a mod matches the rule if ANY matcher hits):
--   modNames       set of exact mod names                      { MinionModifier = true }
--   modPatterns    list of Lua patterns tested on mod.name     { "^EnergyShield" }
--   excludePatterns list of Lua patterns; a mod name matching any of these is never matched by
--                  modNames/modPatterns of this rule (flag/skill matchers still apply)
--   modFlags       ModFlag bit mask tested against mod.flags
--   keywordFlags   KeywordFlag bit mask tested against mod.keywordFlags
--   skillTypes     list of SkillType values; matched against "SkillType" mod tags and against the
--                  skill types of skills/supports granted by the mod (ExtraSkill / ExtraSupport)
--   gemKeywords    set of gem keywords for "+level / +quality of <keyword> gems" mods (GemProperty)
--   skillNames     list of skill names; matched against "SkillName" mod tags and granted skills
--   textPatterns   list of Lua patterns tested on the lower-cased line text, ONLY for lines the
--                  mod parser could not fully understand (fallback for unsupported modifiers)
--   textAlways     also test textPatterns on lines that were parsed
--   parent         id of the parent tag; matching this rule also grants the parent tag. Rules whose
--                  parent is "minion" are additionally evaluated inside MinionModifier mods.
--
-- Mods wrapped in MinionModifier only ever produce the "minion" tag, so that e.g.
-- "Minions deal 20% increased Fire Damage" is not tagged as a player fire damage modifier.

local function elementRule(id, label, element, skillType, keyword)
	return {
		id = id, label = label, category = "Damage",
		modPatterns = { "^"..element.."Damage", "^"..element.."Min$", "^"..element.."Max$", element.."Penetration", "ConvertTo"..element, "GainAs"..element, "^"..element.."Dot", "^"..element.."DegenMultiplier" },
		excludePatterns = { "Taken", "Resist", "Reduction", "AsExtra.*Taken" },
		keywordFlags = keyword,
		skillTypes = { skillType },
		gemKeywords = { [element:lower()] = true },
	}
end

-- Minion type sub-tags. Text patterns are also checked on parsed lines (textAlways) because many
-- minion-type modifiers parse to a generic MinionModifier.
local function minionType(id, label, limitNames, skillNames, textPatterns, skillTypes)
	local modNames = { }
	for _, name in ipairs(limitNames) do
		modNames[name] = true
	end
	return {
		id = id, label = label, category = "Minion Type", parent = "minion",
		modNames = modNames,
		skillNames = skillNames,
		skillTypes = skillTypes,
		textPatterns = textPatterns,
		textAlways = true,
	}
end

return {
	-- Archetypes
	{
		id = "minion", label = "Minion", category = "Archetype",
		modNames = { MinionModifier = true, MinionPerSkillModifier = true },
		modPatterns = { "^Minion", "^Active%a+Limit$" },
		excludePatterns = { "^ActiveTotemLimit$", "^ActiveBallistaLimit$", "^ActiveTrapLimit$", "^ActiveMineLimit$", "^ActiveBrandLimit$" },
		keywordFlags = KeywordFlag.Minion,
		skillTypes = { SkillType.Minion, SkillType.CreatesMinion },
		gemKeywords = { minion = true },
		textPatterns = { "minion", "zombie", "spectre", "skeleton", "golem", "raging spirit", "animated guardian", "animated weapon" },
	},
	-- Minion types (sub-tags of Minion)
	minionType("zombie", "Zombie", { "ActiveZombieLimit" }, { "Raise Zombie" }, { "zombie" }),
	minionType("skeleton", "Skeleton", { "ActiveSkeletonLimit" }, { "Summon Skeletons", "Summon Skeletons of Archers", "Summon Skeletons of Mages", "Vaal Summon Skeletons" }, { "skeleton" }),
	minionType("spectre", "Spectre", { "ActiveSpectreLimit" }, { "Raise Spectre" }, { "spectre" }),
	minionType("golem", "Golem", { "ActiveGolemLimit" }, { }, { "golem" }, { SkillType.Golem }),
	minionType("ragingspirit", "Raging Spirit", { "ActiveRagingSpiritLimit" }, { "Summon Raging Spirit", "Summon Raging Spirit of Enormity" }, { "raging spirit" }),
	minionType("animated", "Animated Weapon/Guardian", { "ActiveAnimatedWeaponLimit" }, { "Animate Weapon", "Animate Guardian" }, { "animated weapon", "animated guardian", "animate weapon", "animate guardian" }),
	minionType("phantasm", "Phantasm", { "ActivePhantasmLimit" }, { "Summon Phantasm" }, { "phantasm" }),
	minionType("holyrelic", "Holy Relic", { "ActiveHolyRelicLimit" }, { "Summon Holy Relic", "Summon Holy Relic of Conviction" }, { "holy relic" }),
	minionType("sentinel", "Sentinel", { "ActiveSentinelOfPurityLimit", "ActiveSentinelOfDominanceLimit", "ActiveSentinelOfAbsolutionLimit" }, { "Summon Sentinel of Radiance", "Herald of Purity", "Dominating Blow", "Absolution" }, { "sentinel" }),
	minionType("spider", "Spider", { "ActiveSpiderLimit" }, { "Raise Spiders" }, { "raise spiders", "spider minion" }),
	minionType("reaper", "Reaper", { "ActiveReaperLimit" }, { "Summon Reaper", "Summon Reaper of Eviscerating", "Summon Reaper of Revenants" }, { "reaper" }),
	{
		id = "totem", label = "Totem", category = "Archetype",
		modNames = { ActiveTotemLimit = true, ActiveBallistaLimit = true },
		modPatterns = { "^Totem" },
		keywordFlags = KeywordFlag.Totem,
		skillTypes = { SkillType.SummonsTotem },
		gemKeywords = { totem = true },
		textPatterns = { "totem", "ballista" },
	},
	{
		id = "trapmine", label = "Trap & Mine", category = "Archetype",
		modNames = { ActiveTrapLimit = true, ActiveMineLimit = true },
		modPatterns = { "^Trap", "^Mine" },
		keywordFlags = bit.bor(KeywordFlag.Trap, KeywordFlag.Mine),
		skillTypes = { SkillType.Trapped, SkillType.RemoteMined },
		gemKeywords = { trap = true, mine = true },
		textPatterns = { "trap", "mine" },
	},
	{
		id = "brand", label = "Brand", category = "Archetype",
		modNames = { ActiveBrandLimit = true },
		modPatterns = { "^Brand" },
		keywordFlags = KeywordFlag.Brand,
		skillTypes = { SkillType.Brand },
		gemKeywords = { brand = true },
		textPatterns = { "brand" },
	},
	{
		id = "aura", label = "Aura", category = "Archetype",
		modPatterns = { "^Aura", "AuraEffect" },
		keywordFlags = KeywordFlag.Aura,
		skillTypes = { SkillType.Aura },
		gemKeywords = { aura = true },
		textPatterns = { "aura" },
	},
	{
		id = "curse", label = "Curse", category = "Archetype",
		modPatterns = { "^Curse", "CurseEffect", "EnemyCurseLimit", "^Hex" },
		keywordFlags = KeywordFlag.Curse,
		skillTypes = { SkillType.AppliesCurse, SkillType.Hex, SkillType.Mark },
		gemKeywords = { curse = true, hex = true, mark = true },
		textPatterns = { "curse", "hex" },
	},
	{
		id = "warcry", label = "Warcry", category = "Archetype",
		modPatterns = { "^Warcry" },
		keywordFlags = KeywordFlag.Warcry,
		skillTypes = { SkillType.Warcry },
		gemKeywords = { warcry = true },
		textPatterns = { "warcr" },
	},
	{
		id = "attack", label = "Attack", category = "Archetype",
		modFlags = ModFlag.Attack,
		keywordFlags = KeywordFlag.Attack,
		modNames = { Accuracy = true },
		skillTypes = { SkillType.Attack },
		gemKeywords = { attack = true },
	},
	{
		id = "spell", label = "Spell", category = "Archetype",
		modFlags = ModFlag.Spell,
		keywordFlags = KeywordFlag.Spell,
		modPatterns = { "^Spell" },
		excludePatterns = { "^SpellSuppression", "^SpellBlock", "^SpellDodge" },
		skillTypes = { SkillType.Spell },
		gemKeywords = { spell = true },
	},

	-- Damage types
	{
		id = "physical", label = "Physical", category = "Damage",
		modPatterns = { "^PhysicalDamage", "^PhysicalMin$", "^PhysicalMax$", "^PhysicalDot", "PhysicalPenetration" },
		excludePatterns = { "Taken", "Reduction", "ConvertTo", "GainAs" },
		keywordFlags = KeywordFlag.Physical,
		skillTypes = { SkillType.Physical },
		gemKeywords = { physical = true },
	},
	elementRule("fire", "Fire", "Fire", SkillType.Fire, KeywordFlag.Fire),
	elementRule("cold", "Cold", "Cold", SkillType.Cold, KeywordFlag.Cold),
	elementRule("lightning", "Lightning", "Lightning", SkillType.Lightning, KeywordFlag.Lightning),
	elementRule("chaos", "Chaos", "Chaos", SkillType.Chaos, KeywordFlag.Chaos),
	{
		id = "elemental", label = "Elemental", category = "Damage",
		modPatterns = { "^ElementalDamage", "ElementalPenetration", "GainAsElemental" },
		excludePatterns = { "Taken", "Reduction" },
		gemKeywords = { elemental = true },
	},
	{
		id = "dot", label = "Damage over Time", category = "Damage",
		modFlags = ModFlag.Dot,
		keywordFlags = bit.bor(KeywordFlag.PhysicalDot, KeywordFlag.FireDot, KeywordFlag.ColdDot, KeywordFlag.LightningDot, KeywordFlag.ChaosDot),
		modPatterns = { "DotMultiplier", "^%a*Dot$" },
		skillTypes = { SkillType.DamageOverTime },
	},
	{
		id = "crit", label = "Critical Strike", category = "Damage",
		modPatterns = { "^Crit" },
		textPatterns = { "critical strike" },
	},

	-- Ailments
	{
		id = "bleed", label = "Bleed", category = "Ailment",
		modPatterns = { "^Bleed", "BleedChance" },
		keywordFlags = KeywordFlag.Bleed,
		textPatterns = { "bleed" },
	},
	{
		id = "poison", label = "Poison", category = "Ailment",
		modPatterns = { "^Poison", "PoisonChance" },
		keywordFlags = KeywordFlag.Poison,
		textPatterns = { "poison" },
	},
	{
		id = "ignite", label = "Ignite", category = "Ailment",
		modPatterns = { "^Ignite", "EnemyIgnite" },
		keywordFlags = KeywordFlag.Ignite,
		textPatterns = { "ignite" },
	},
	{
		id = "freeze", label = "Freeze & Chill", category = "Ailment",
		modPatterns = { "^Freeze", "^Chill", "EnemyFreeze", "EnemyChill" },
		textPatterns = { "freez", "chill" },
	},
	{
		id = "shock", label = "Shock", category = "Ailment",
		modPatterns = { "^Shock", "EnemyShock" },
		textPatterns = { "shock" },
	},

	-- Defences
	{
		id = "life", label = "Life", category = "Defence",
		modPatterns = { "^Life" },
		excludePatterns = { "Cost", "Reserv", "^LifeConvertTo", "Degen" },
	},
	{
		id = "mana", label = "Mana", category = "Defence",
		modPatterns = { "^Mana" },
		excludePatterns = { "Cost", "Reserv", "Degen" },
	},
	{
		id = "energyshield", label = "Energy Shield", category = "Defence",
		modPatterns = { "^EnergyShield", "AndEnergyShield$" },
		excludePatterns = { "Cost", "Degen" },
	},
	{
		id = "armour", label = "Armour", category = "Defence",
		modPatterns = { "^Armour", "PhysicalDamageReduction" },
	},
	{
		id = "evasion", label = "Evasion", category = "Defence",
		modPatterns = { "^Evasion", "AndEvasion$" },
	},
	{
		id = "block", label = "Block", category = "Defence",
		modPatterns = { "BlockChance" },
	},
	{
		id = "resistance", label = "Resistances", category = "Defence",
		modPatterns = { "^%a*Resist$", "^%a*ResistMax$" },
		excludePatterns = { "^Enemy" },
	},
	{
		id = "suppression", label = "Spell Suppression", category = "Defence",
		modPatterns = { "^SpellSuppression" },
	},

	-- Utility
	{
		id = "movement", label = "Movement Speed", category = "Utility",
		modNames = { MovementSpeed = true },
	},
	{
		id = "charges", label = "Charges", category = "Utility",
		modPatterns = { "^PowerCharge", "^FrenzyCharge", "^EnduranceCharge", "^ChargeDuration" },
		textPatterns = { "power charge", "frenzy charge", "endurance charge" },
	},
	{
		id = "flask", label = "Flask", category = "Utility",
		modPatterns = { "^Flask" },
		textPatterns = { "flask" },
	},
}
