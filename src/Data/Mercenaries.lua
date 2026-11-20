-- Path of Building
--
-- Mercenary roster (Mercenaries of Trarthus). Each class has fixed skill pools: all primary skills,
-- plus a fixed number of secondary and utility skills rolled from their lists. A hired mercenary is
-- described by its class and the skills it rolled.
--
-- Source: PoE Wiki "Mercenary" (List of mercenary classes), read 2026-11-20,
-- https://www.poewiki.net/wiki/Mercenary - CC BY-NC 3.0. Support counts: N(one) L(ow) M(edium) H(igh).
--
-- Mercenary skills are not gems: the wiki notes their numbers may differ from the gem versions and
-- are not affected by gem level or quality. tools/lib/mercenary.lua calculates them from the gem
-- versions (default level 20, quality 0) as an estimate until values are confirmed in play.

local M = { }

-- What a mercenary skill does for the player's calculation
--   aura      ally aura: reaches you and your minions (calculated)
--   vaalaura  temporary ally aura (calculated only when asked for)
--   curse     curse on enemies (calculated; shares the enemy's curse slots)
--   mark      mark on enemies (calculated)
--   ally      affects you or enemies but is not calculated yet (warcries, links, debuffs, ...)
--   (absent)  the mercenary's own attack, movement or self buff
M.skillEffects = {
	["Anger"] = "aura", ["Clarity"] = "aura", ["Determination"] = "aura", ["Discipline"] = "aura", ["Envy"] = "aura",
	["Grace"] = "aura", ["Haste"] = "aura", ["Hatred"] = "aura", ["Malevolence"] = "aura", ["Precision"] = "aura",
	["Pride"] = "aura", ["Purity of Fire"] = "aura", ["Purity of Ice"] = "aura", ["Purity of Lightning"] = "aura",
	["Vitality"] = "aura", ["Wrath"] = "aura", ["Zealotry"] = "aura",
	["Vaal Grace"] = "vaalaura",
	["Conductivity"] = "curse", ["Despair"] = "curse", ["Elemental Weakness"] = "curse", ["Flammability"] = "curse",
	["Frostbite"] = "curse", ["Punishment"] = "curse", ["Temporal Chains"] = "curse",
	["Blasphemy Flammability"] = "curse", ["Blasphemy Enfeeble"] = "curse",
	["Alchemist's Mark"] = "mark", ["Assassin's Mark"] = "mark", ["Poacher's Mark"] = "mark",
	["Abyssal Cry"] = "ally", ["Bane"] = "ally", ["Battlemage's Cry"] = "ally", ["Consecrated Path"] = "ally",
	["Enduring Cry"] = "ally", ["Flame Link"] = "ally", ["Frost Bomb"] = "ally", ["Incite"] = "ally",
	["Infernal Cry"] = "ally", ["Inspiring Cry"] = "ally", ["Intimidating Cry"] = "ally", ["Proximity Shield"] = "ally",
	["Rallying Cry"] = "ally", ["Relic of Binding"] = "ally", ["Steelskin Ally"] = "ally", ["Summon Holy Relic"] = "ally",
	["Vaal Ancestral Warchief"] = "ally", ["Wither Totem"] = "ally", ["Withering Step"] = "ally",
}

-- Skills calculated through a gem with supports (curse auras)
M.skillGems = {
	["Blasphemy Flammability"] = { gem = "Flammability", supports = { "Blasphemy" } },
	["Blasphemy Enfeeble"] = { gem = "Enfeeble", supports = { "Blasphemy" } },
}

-- Mercenary-exclusive supports that change what reaches the player (others only change the mercenary's own skills)
M.supports = {
	["Curse Effect III"] = { curseEffect = 20, text = "20% increased Effect of Supported Curses" },
}

local function class(name, house, attributes, weapons, infamous, primary, secondary, utility, note)
	return { name = name, house = house, attributes = attributes, weapons = weapons, infamous = infamous,
		primary = primary, secondary = secondary, utility = utility, note = note }
end
local function pick(count, list) return { pick = count, options = list } end

M.classes = {
	-- Strength (Marauders), House Keita
	class("Earthshaker", "Keita", "Str", "2H Mace, 2H Axe", true,
		{ "Intimidating Cry", "Leap Slam" },
		pick(2, { "Earthquake of Amplification", "Ground Slam", "Sunder of Trarthus", "Vaal Ground Slam", "Tectonic Cascade" }),
		pick(2, { "Vaal Vitality", "Burrow", "Determination", "Molten Shell", "Endure" })),
	class("Eruptor", "Keita", "Str", "2H Axe, 2H Mace", true,
		{ "Infernal Cry", "Leap Slam", "Triggerslam" },
		pick(2, { "Tectonic Slam", "Consecrated Path", "Ashen Fissure", "Volcanic Fissure of Snaking" }),
		pick(1, { "Herald of Ash", "Determination", "Flame Link", "Molten Shell", "Purity of Fire" })),
	class("Ripper", "Keita", "Str", "1H Axe, 1H Sword, 1H Thrusting Sword", true,
		{ "Tunnelslam", "Enrage" },
		pick(2, { "Slicing Wind", "Cleave", "Vaal Cleave", "Leap Slam of Groundbreaking", "Chain Hook of Trarthus" }),
		pick(2, { "Vitality", "Determination", "Molten Shell", "Leap Slam" })),
	class("Smoulderstrike", "Keita", "Str", "1H Axe, 1H Sword, 1H Mace, 1H Thrusting Sword", false,
		{ "Punishment", "Inflame" },
		pick(2, { "Infernal Blow of Immolation", "Vaal Molten Strike", "Molten Strike", "Flamebolt Strike" }),
		pick(2, { "Leap Slam", "Infernal Cry", "Molten Shell", "Flame Aegis", "Anger" })),
	class("Striker", "Keita", "Str", "1H Mace, 1H Axe", true,
		{ "Vigilant Strike", "Enduring Cry", "Physical Aegis" },
		pick(1, { "Heavy Strike of Vulnerability", "Boneshatter", "Dual Strike" }),
		pick(2, { "Molten Shell", "Vitality", "Leap Slam", "Decoy Totem", "Determination", "Vaal Ancestral Warchief" })),
	-- Dexterity (Rangers), House Cyaxan
	class("Flamequiver", "Cyaxan", "Dex", "Bow, Quiver", true,
		{ "Burning Arrow", "Alchemist's Mark" },
		pick(2, { "Explosive Arrow", "Molten Well", "Artillery Ballista", "Blast Rain of Trarthus", "Vaal Burning Arrow", "Conflagration" }),
		pick(2, { "Blasphemy Flammability", "Grace", "Dash", "Blink Arrow" })),
	class("Manyshot", "Cyaxan", "Dex", "Bow, Quiver", true,
		{ "Ice Shot", "Vaal Grace" },
		pick(2, { "Mirror Arrow", "Icicle Rain", "Vaal Ice Shot", "Frigid Forkshot" }),
		pick(2, { "Hatred", "Grace", "Blink Arrow", "Dash", "Frost Bomb" })),
	class("Sniper", "Cyaxan", "Dex", "Bow, Quiver", true,
		{ "Ensnaring Arrow", "Poacher's Mark" },
		pick(2, { "Barrage of Volley Fire", "Split Arrow", "Tornado Shot", "Puncture", "Rain of Arrows of Saturation", "Shrapnel Ballista", "Siege Ballista of Trarthus", "Greater Split Arrow" }),
		pick(2, { "Haste", "Dash", "Frenzy", "Blink Arrow", "Grace" })),
	class("Thunderquiver", "Cyaxan", "Dex", "Bow, Quiver", false,
		{ "Lightning Arrow", "Assassin's Mark" },
		pick(2, { "Storm Rain", "Galvanic Arrow", "Vaal Lightning Arrow", "Greater Lightning Arrow" }),
		pick(2, { "Dash", "Precision", "Blink Arrow", "Trarthan Agility", "Wrath" })),
	class("Toxicologist", "Cyaxan", "Dex", "Bow, Quiver", true,
		{ "Withering Step", "Chaotic Burst", "Chaotic Shot" },
		pick(1, { "Caustic Arrow", "Scourge Arrow of Menace", "Toxic Rain", "Vaal Caustic Arrow" }),
		pick(2, { "Malevolence", "Dash", "Trarthan Agility", "Grace", "Blink Arrow" })),
	-- Intelligence (Witches), House Cyaxan
	class("Cruel Mistress", "Cyaxan", "Int", "Staff", true,
		{ "Despair", "Void Sphere" },
		pick(2, { "Dark Bargain", "Soulrend of Reaping", "Profane Cascade", "Voltaxic Burst", "Summon Seeking Void", "Forbidden Rite Totem" }),
		pick(2, { "Zealotry", "Envy", "Flame Dash", "Lightning Warp", "Frostblink" })),
	class("Flamehand", "Cyaxan", "Int", "Wand, (Shield), Rune Dagger, Sceptre", false,
		{ "Flame Wall", "Flammability" },
		pick(2, { "Flameblast", "Fireball", "Rolling Magma", "Fireball of Impact", "Greater Flame Dash", "Vaal Flameblast", "Flame Surge" }),
		pick(2, { "Flame Aegis", "Purity of Fire", "Frostblink", "Lightning Warp", "Anger" })),
	class("Frosthand", "Cyaxan", "Int", "Wand, (Shield), Rune Dagger, Sceptre", true,
		{ "Frost Bomb", "Frostbite" },
		pick(2, { "Eye of Winter", "Frostbolt", "Ice Nova of Projection", "Ice Nova", "Frost Wall", "Vortex", "Icestorm" }),
		pick(2, { "Discipline", "Purity of Ice", "Lightning Warp", "Frostblink", "Flame Dash" })),
	class("Reanimator", "Cyaxan", "Int", "Wand, Shield, Rune Dagger, Sceptre", true,
		{ "Raise Zombie of Gigantism", "Desecrate" },
		pick(2, { "Summon Raging Spirit", "Raise Zombie of Falling", "Bone Offering", "Summon Skeletons", "Flesh Offering" }),
		pick(2, { "Blasphemy Enfeeble", "Relic of Binding", "Flame Dash", "Frostblink", "Lightning Warp" })),
	class("Stormhand", "Cyaxan", "Int", "Wand, (Shield), Rune Dagger, Sceptre", true,
		{ "Conductivity", "Sigil of Power" },
		pick(2, { "Spark", "Ball Lightning of Static", "Greater Shock Nova", "Orb of Storms", "Arc", "Storm Call", "Greater Stormcall" }),
		pick(2, { "Purity of Lightning", "Proximity Shield", "Wrath", "Lightning Warp", "Flame Dash", "Frostblink" })),
	class("Withertouch", "Cyaxan", "Int", "Staff", true,
		{ "Bane", "Temporal Chains" },
		pick(2, { "Essence Drain of Wickedness", "Blight", "Greater Soulrend", "Scourstorm", "Altar of Chaos" }),
		pick(2, { "Clarity", "Withering Step", "Frostblink", "Malevolence", "Lightning Warp", "Wither Totem", "Flame Dash" })),
	-- Strength / Intelligence (Templars), House Keita
	class("Cardinal", "Keita", "Str/Int", "Staff, Warstaff", true,
		{ "Holy Hammers", "Holy Strike" },
		pick(2, { "Holy Sweep", "Consecrated Path", "Sanctified Strike" }),
		pick(2, { "Herald of Purity", "Wrath", "Flame Dash", "Purity of Lightning" })),
	class("Fallen Reverend", "Keita", "Str/Int", "Wand, Sceptre, (Shield)", true,
		{ "Absolution", "Raise Spectre of Transience", "Desecrate" },
		pick(1, { "Reinforce: Fallen Osseotitan", "Reinforce: Fallen Bishop", "Reinforce: Fallen Emperor" }),
		pick(2, { "Battlemage's Cry", "Frostblink", "Wrath", "Zealotry", "Flame Dash" })),
	class("Flaming Charlatan", "Keita", "Str/Int", "Sceptre, Wand", false,
		{ "Holy Flame Totem", "Purifying Flame" },
		pick(2, { "Holy Mortar", "Meteor", "Wave of Conviction of Trarthus", "Scorching Ray" }),
		pick(2, { "Herald of Ash", "Anger", "Flame Dash", "Lightning Warp" }), "Holy Mortar is always one of the secondary skills"),
	class("Storming Zealot", "Keita", "Str/Int", "Staff", true,
		{ "Unnerving Blast", "Wave of Conviction" },
		pick(2, { "Divine Ire", "Shockwave Totem of Shocking", "Tornado of Elemental Turbulence", "Divine Retribution" }),
		pick(2, { "Wrath", "Lightning Warp", "Flame Dash" }), "Divine Ire and Wrath are always rolled"),
	class("Warpriest", "Keita", "Str/Int", "1H Mace, Sceptre, Shield", true,
		{ "Summon Holy Relic", "Smite" },
		pick(2, { "Raise Spectre: Holy Flame Elementals", "Dominating Blow", "Beacons of Faith", "Touch of God" }),
		pick(2, { "Flame Dash", "Herald of Purity", "Purity of Lightning" })),
	class("Winter Deacon", "Keita", "Str/Int", "2H Mace, Staff", false,
		{ "Frost Shield", "Vaal Glacial Hammer" },
		pick(2, { "Glacial Hammer", "Heavy Strike of Trarthus", "Earthquake of Winter", "Ice Crash" }),
		pick(2, { "Hatred", "Arctic Armour", "Purity of Ice", "Frost Bomb", "Frostblink" })),
	-- Strength / Dexterity (Duelists), House Azadi
	class("Bastion", "Azadi", "Str/Dex", "1H Axe, 1H Sword, 1H Mace, Shield", true,
		{ "Shield Crush", "Shield Charge" },
		pick(2, { "Tempest Shield", "Prismplate", "Spectral Shield Throw of Trarthus" }),
		pick(2, { "Determination", "Dash", "Physical Aegis", "Intimidating Cry", "Impenetrable Bastion" })),
	class("Bloodletter", "Azadi", "Str/Dex", "1H Axe, 1H Sword", true,
		{ "Bloodthirst", "Blood Mortar", "Lacerate" },
		pick(1, { "Perforate", "Bladestorm" }),
		pick(2, { "Leap Slam", "Determination", "Dash", "Oil Slick" })),
	class("Combatant", "Azadi", "Str/Dex", "1H Axe, 1H Sword, Claw", true,
		{ "Inspiring Cry", "Herald of Ice" },
		pick(2, { "Wild Strike", "Spectral Helix", "Frost Blades", "Static Strike" }),
		pick(2, { "Dash", "Wrath", "Purity of Ice", "Frostblink" })),
	class("Shattersword", "Azadi", "Str/Dex", "1H Axe, 1H Sword", false,
		{ "Call of Steel", "Rallying Cry", "Triggerblades" },
		pick(1, { "Lancing Steel", "Splitting Steel", "Shattering Steel" }),
		pick(2, { "Whirling Blades", "Grace", "Dash", "Brutal Teachings" })),
	class("Swiftblade", "Azadi", "Str/Dex", "2H Axe, 2H Sword", true,
		{ "Cyclone of the Empire", "Rallying Cry", "Triggerblades" },
		pick(1, { "Flicker Strike", "Vaal Double Strike" }),
		pick(2, { "Dash", "Steelskin Ally", "Incite", "Pride", "Leap Slam" })),
	-- Dexterity / Intelligence (Shadows), House Azadi
	class("Bladebitter", "Azadi", "Dex/Int", "1H Sword, Claw, Dagger", true,
		{ "Viper Strike", "Abyssal Cry" },
		pick(2, { "Venom Gyre", "Pestilent Strike", "Profane Strike", "Cobra Lash" }),
		pick(2, { "Grace", "Withering Step", "Dash", "Whirling Blades", "Malevolence" })),
	class("Bladecaster", "Azadi", "Dex/Int", "Wand, (Shield), Dagger", true,
		{ "Clutches of the Damned", "Bloody Warp" },
		pick(2, { "Blade Vortex", "Ethereal Knives", "Bladefall", "Bladefall of Trarthus", "Seismic Crush" }),
		pick(2, { "Flame Dash", "Aspect of the Spider", "Dash", "Grace", "Frost Shield" })),
	class("Blade Ambusher", "Azadi", "Dex/Int", "1H Sword, Claw, Dagger", true,
		{ "Blade Trap", "Trarthan Agility" },
		pick(2, { "Spectral Helix of Trarthus", "Spectral Throw of Trarthus" }),
		pick(2, { "Grace", "Flame Dash", "Bear Trap", "Summon Skitterbots", "Smoke Mine" })),
	class("Frost Ambusher", "Azadi", "Dex/Int", "Wand, Sceptre, Dagger, Shield", false,
		{ "Frost Shield", "Greater Vortex Trap" },
		pick(1, { "Ice Trap", "Creeping Frost" }),
		pick(2, { "Arctic Armour", "Summon Skitterbots", "Grace", "Vaal Arctic Armour", "Flame Dash", "Frostblink" }), "at most 5 skills"),
	class("Shock Ambusher", "Azadi", "Dex/Int", "Wand, Sceptre, Dagger", true,
		{ "Conductivity", "Vaal Lightning Trap" },
		pick(2, { "Lightning Trap", "Lightning Warp", "Ball Lightning of Orbiting", "Lightning Spire Trap" }),
		pick(2, { "Summon Skitterbots", "Smoke Mine", "Zealotry", "Frostblink", "Flame Dash" })),
	-- Strength / Dexterity / Intelligence (Scions), House Bardiya
	class("Kineticist", "Bardiya", "Str/Dex/Int", "Wand, Shield", true,
		{ "Elemental Weakness", "Flame Wall" },
		pick(2, { "Greater Kinetic Blast", "Kinetic Rain of Impact", "Kinetic Bolt", "Kinetic Blast of Clustering", "Barrage" }),
		pick(2, { "Inspiring Cry", "Haste", "Frostblink", "Flame Dash" })),
	class("Sanguimancer", "Bardiya", "Str/Dex/Int", "Wand, (Shield)", true,
		{ "Boiling Blood", "Storm Call of Trarthus", "Bodyswap" },
		pick(1, { "Corrupted Blade Vortex of the Scythe", "Exsanguinate", "Reap", "Vaal Reap" }),
		pick(2, { "Proximity Shield", "Vaal Vitality", "Flame Dash", "Pride", "Lightning Warp" })),
	-- Special
	class("Mysterious Diver", "Special", "Str/Dex", "1H Sword, 1H Thrusting Sword, 1H Axe, Claw", true,
		{ "Elemental Hit of Ice", "Frost Bomb" },
		pick(2, { "Frost Blades", "Herald of Ice", "Wild Strike" }),
		pick(2, { "Hatred", "Purity of Ice", "Frostblink", "Dash" }), "only in the Diving Shoals area (Curse of the Allflame)"),
	class("Chaplain of the Well", "Special", "Str/Int", "Staff, 1H Warstaff", false,
		{ "Abyssal Spray", "Abyssal Spray Detonation", "Power of the Depths" },
		pick(1, { "Smite", "Vaal Smite" }),
		pick(2, { "Envy", "Flame Dash", "Abyssal Cry", "Herald of Ash" }), "spawns next to a mercenary encounter near an Abyss"),
}

M.byName = { }
for _, c in ipairs(M.classes) do
	M.byName[c.name:lower()] = c
end

return M
