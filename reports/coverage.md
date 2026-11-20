# Modifier coverage: all uniques and passive tree

Path of Building 2.68.1 · passive tree 3_30 · generated 2026-11-20 16:41

A line is **unsupported** when Path of Building cannot parse it, so it is not part of any calculation. 
**Impact** is an estimate: *Offence* / *Defence* lines may change your numbers, *Utility* / *Cosmetic* lines usually do not. 
**Game stat id** is the official identifier of the effect (empty if the text could not be matched).

## Summary

| Scope | Lines | Unsupported | With game stat id | Offence | Defence | Utility | Cosmetic | Sources with a gap |
|---|---|---|---|---|---|---|---|---|
| Unique items | 7279 | 804 (11.0%) | 640 | 268 | 190 | 330 | 16 | 547 of 1335 |
| Passive nodes | 5092 | 301 (5.9%) | 256 | 130 | 92 | 79 | 0 | 238 of 1750 |

## Changes since the previous report

- Newly unsupported: **0**
- Now supported: **0**
- Unsupported lines that disappeared from the data: **0**

## Passive tree 3_30 compared with 3_29

New line texts in this tree: 110 supported, **20 unsupported**.

| Source | Where | Line | Impact | Game stat id |
|---|---|---|---|---|
| Blackflame | Reliquarian | Withered does not expire on Enemies Ignited by you | Offence | `enemies_you_ignite_wither_does_not_expire` |
| Chain Reaction | Saboteur | When your Traps Trigger, your Traps within 2 metres also Trigger | Offence | `nearby_traps_within_x_units_also_trigger_on_triggering_trap` |
| Demolitions Specialist | Saboteur | Mines Hinder Enemies within 3 metres for 2 seconds when they Land | Offence | `mines_hinder_nearby_enemies_for_x_ms_on_arming` |
| Disorienting Display | Notable | 10% chance to Blind Enemies within 6 metres when you use an Elemental Skill | Utility | `elemental_skill_chance_to_blind_nearby_enemies_%` |
| Fearsome Warrior | Notable | 25% chance to Intimidate Enemies within 4 metres for 4 seconds on Melee Kill | Utility | `chance_to_intimidate_nearby_enemies_on_melee_kill_%` |
| Focal Point | Deadeye | Your Mark Transfers to another Enemy within 3 metres when Marked Enemy dies | Utility | `your_marks_transfer_to_nearby_enemies_on_death_%_chance` |
| Foulborn Tremor Rod | Reliquarian | Mines can be Detonated an additional time | Offence | `mine_extra_uses` |
| Frigid Wake | Occultist | Every 4 seconds, 50% chance to Freeze Non-Frozen Enemies within 6 metres for 0.4 seconds | Offence | `every_4_seconds_%_chance_freeze_non_frozen_enemies_for_300ms` |
| Golden Glory | Luminary | Increases and Reductions to Light Radius also apply to Effect of | Utility | — |
| Golden Glory | Luminary | your Link Skill Buffs on your Mercenary at 50% of their value | Utility | — |
| Master Alchemist | Pathfinder | Removes Ailments when you use a Flask | Defence | `dispel_status_ailments_on_flask_use` |
| Perfect Crime | Saboteur | Grants Level 20 Summon Triggerbots | Offence | — |
| Snaring Spirits | Notable | Totems Hinder Enemies within 3 metres of them when Summoned | Offence | `totem_hinder_nearby_enemies_when_summoned_with_25%_reduced_movement_speed` |
| That didn't happen! | Delirious | Non-Cluster, Non-Passage, Non-Mycelium Jewels Socketed in your Passive Skill Tree have no effect | Utility | `socketed_non_cluster_jewels_have_no_effect` |
| The Crustacean's Call | Reliquarian | Skills Supported by Spell Totem are Crab Totems | Offence | `spell_totems_are_crab_totems` |
| The Draugur's Lantern | Reliquarian | Draugurflames burn enemies around you for 8 seconds after you Ignite a target | Offence | `has_ghost_furnace` |
| The Living Blade | Reliquarian | 10% chance to remove 1 Mana Burn on Kill | Utility | `chance_to_remove_1_tincture_toxicity_on_kill_%` |
| The Monastery Bell | Reliquarian | Count as Blocking Attack Damage from the first target Hit with each Shield Attack | Defence | `count_as_blocking_attack_from_shield_attack_first_target` |
| Tide Caller | Brinerot | Grants Level 20 Surging Torrent | Utility | — |
| Tidebreaker | Reliquarian | Gain an Endurance Charge when you Stun an Enemy with a Melee Hit | Defence | `gain_endurance_charge_on_melee_stun`, `gain_endurance_charge_on_melee_stun_%` |

## Unsupported · Offence (398)

| Source | Where | Line | Impact | Game stat id |
|---|---|---|---|---|
| Abberath's Hooves | Boots | When you Kill an Ignited Enemy, inflict an equivalent Ignite on each Enemy within 2 metres | Offence | `ignite_X_nearby_enemies_for_4_s_on_killing_ignited_enemy` |
| Admiral's Arrogance | Gloves | (10-20)% chance that if you would gain Rage on Hit, you instead gain up to your maximum Rage | Offence | `gain_max_rage_on_rage_gain_from_hit_%_chance` |
| Akoya's Gaze | Helmet | Non-Exerted Attacks deal no Damage | Offence | `non_exerted_attacks_deal_no_damage` |
| Alberon's Warpath | Boots | Summon Skeletons cannot Summon more than 1 Skeleton Warrior | Offence | — |
| Anathema | Ring | (10-20)% chance to gain a Power Charge when you Cast a Curse Spell | Offence | `gain_power_charge_on_curse_cast_%` |
| Apex Mode | Jewel | Spells which have gained Intensity Recently gain 1 Intensity every 0.5 Seconds | Offence | `skills_gain_intensity_every_x_milliseconds_if_gained_intensity_recently` |
| Asenath's Gentle Touch | Gloves | Non-Aura Curses you inflict are not removed from Dying Enemies | Offence | `curses_you_inflict_remain_after_death` |
| Ashcaller | Wand | 10% chance to Cover Enemies in Ash on Hit | Offence | `cover_in_ash_on_hit_%` |
| Ashes of the Stars | Amulet | (5-10)% increased Experience Gain of Gems | Offence | `gem_experience_gain_+%` |
| Asphyxia's Wrath | Quiver | Hexes Transfer to all Enemies within 3 metres when Hexed Enemy dies | Offence | `transfer_hexes_to_X_nearby_enemies_on_kill` |
| Atziri's Disfavour | Two Handed Axe | 25% chance to Maim on Hit | Offence | `local_maim_on_hit_%` |
| Atziri's Reign | Jewel | Vaal Skills have (15-20)% chance to regain consumed Souls when used | Offence | `vaal_skill_soul_refund_chance_%` |
| Badge of the Brotherhood | Amulet | (20-25)% chance to lose a Frenzy Charge when you use a Travel Skill | Offence | `lose_a_frenzy_charge_on_travel_skill_use_%_chance` |
| Badge of the Brotherhood | Amulet | (20-25)% chance to lose a Power Charge when you gain Elusive | Offence | `lose_a_power_charge_when_you_gain_elusive_%_chance` |
| Berek's Respite | Ring | When you Kill a Shocked Enemy, inflict an equivalent Shock on each Enemy within 2 metres | Offence | `shock_X_nearby_enemies_for_2_s_on_killing_shocked_enemy` |
| Berek's Respite | Ring | When you Kill an Ignited Enemy, inflict an equivalent Ignite on each Enemy within 2 metres | Offence | `ignite_X_nearby_enemies_for_4_s_on_killing_ignited_enemy` |
| Bino's Kitchen Knife | Dagger | On Killing a Poisoned Enemy, Enemies within 3 metres are Poisoned, and you and | Offence | — |
| Bitter Instinct | Shield | Damaging Retaliation Skills become Usable every 4 seconds | Offence | `retaliation_skills_become_usable_every_x_ms` |
| Bitter Instinct | Shield | Retaliation Skills become Usable for (50-100)% longer | Offence | `retaliation_use_window_duration_+%` |
| Black Zenith | Gloves | Socketed Projectile Spells fire Projectiles in a circle | Offence | `local_display_socketed_spells_projectiles_circle` |
| Blackflame | Ring | Withered does not expire on Enemies Ignited by you | Offence | `enemies_you_ignite_wither_does_not_expire` |
| Blood of Summer | One Handed Sword | 33% chance to gain a Frenzy Charge on Kill | Offence | `add_frenzy_charge_on_kill_%_chance` |
| Bloodgrip | Amulet | Moving while Bleeding doesn't cause you to take extra Damage | Offence | `no_extra_bleed_damage_while_moving` |
| Bound Fate | Belt | Damage of Hits against you is Lucky | Offence | — |
| Brain Rattler | Two Handed Mace | Enemies you Shock have 20% reduced Movement Speed | Offence | `enemies_you_shock_movement_speed_+%` |
| Brain Rattler | Two Handed Mace | Enemies you Shock have 30% reduced Cast Speed | Offence | `enemies_you_shock_cast_speed_+%` |
| Breathstealer | Gloves | Create a Blighted Spore when your Skills or Minions Kill a Rare Monster | Offence | `create_blighted_spore_on_killing_rare_enemy` |
| Brinerot Whalers | Boots | Unaffected by Shocked Ground | Offence | `unaffected_by_shocked_ground` |
| Call of the Brotherhood | Ring | Your spells have 100% chance to Shock against Frozen Enemies | Offence | `spell_chance_to_shock_frozen_enemies_%` |
| Call of the Void | Ring | Enemies Chilled by your Hits can be Shattered as though Frozen | Offence | `chills_from_your_hits_cause_shattering` |
| Callinellus Malleus | One Handed Mace | All Attack Damage Chills when you Stun | Offence | `attack_damage_that_stuns_also_chills` |
| Cane of Unravelling | Staff | Gain a Power Charge after Spending a total of 200 Mana | Offence | `local_display_gain_power_charge_on_spending_mana` |
| Chains of Command | Body Armour | Animated and Manifested Minions' Melee Strikes deal 50% less Splash Damage | Offence | `grant_animated_minion_melee_splash_damage_+%_final_for_splash` |
| Chains of Command | Body Armour | Animated and Manifested Minions' Melee Strikes deal Splash | Offence | — |
| Chains of Command | Body Armour | Damage to surrounding targets | Offence | — |
| Cinderswallow Urn | Flask | Recharges 5 Charges when you Consume an Ignited corpse | Offence | `local_flask_gain_X_charges_on_consuming_ignited_corpse` |
| Cloak of Tawm'r Isley | Body Armour | Minions cannot be Blinded | Offence | `minions_cannot_be_blinded` |
| Cloak of Tawm'r Isley | Body Armour | Minions have 15% chance to Blind Enemies on hit | Offence | `minions_%_chance_to_blind_on_hit` |
| Combat Focus | Jewel | With 40 total Dexterity and Strength in Radius, Prismatic Skills cannot choose Lightning | Offence | `local_unique_jewel_elemental_hit_cannot_roll_lightning_damage_with_40_dex_+_str_in_radius` |
| Combat Focus | Jewel | With 40 total Intelligence and Dexterity in Radius, Prismatic Skills cannot choose Fire | Offence | `local_unique_jewel_elemental_hit_cannot_roll_fire_damage_with_40_int_+_dex_in_radius` |
| Combat Focus | Jewel | With 40 total Strength and Intelligence in Radius, Prismatic Skills cannot choose Cold | Offence | `local_unique_jewel_elemental_hit_cannot_roll_cold_damage_with_40_int_+_str_in_radius` |
| Corona Solaris | Wand | Triggers Level 20 Blinding Aura when Equipped | Offence | `local_display_trigger_level_X_blinding_aura_skill_on_equip` |
| Coward's Chains | Belt | Damage of Enemies Hitting you is Unlucky while you are Cursed with Vulnerability | Offence | `enemy_extra_damage_rolls_while_affected_by_vulnerability` |
| Cowards' Wail | Shield | Maximum (3-5) Spectral Totems | Offence | `number_of_ghost_totems_allowed` |
| Cowards' Wail | Shield | Skills used by Spectral Totems deal (40-50)% less Damage | Offence | `ghost_totem_skill_damage_+%_final` |
| Cowards' Wail | Shield | Totems which would be killed by Enemies become Spectral Totems for 8 seconds instead | Offence | `base_ghost_totem_duration` |
| Curtain Call | Helmet | Mines have (40-50)% increased Detonation Speed | Offence | `mine_detonation_speed_+%` |
| Daresso's Passion | One Handed Sword | 25% chance to gain a Frenzy Charge on Kill | Offence | `add_frenzy_charge_on_kill_%_chance` |
| Death's Hand | Sceptre | 30% chance to gain a Power Charge when you Stun | Offence | `chance_to_gain_power_charge_on_stun_%` |
| Deidbell | Helmet | Skills which Exert an Attack have (20-40)% chance to not count that Attack | Offence | `chance_for_exerted_attacks_to_not_reduce_count_%` |
| Dialla's Malefaction | Body Armour | Gems Socketed in Blue Sockets gain 100% increased Experience | Offence | `local_socketed_gems_in_blue_sockets_experience_gained_+%` |
| Divine Inferno | Jewel | With at least 40 Strength in Radius, Attacks Exerted by Infernal Cry deal (40-60)% more Damage with Ignite | Offence | `local_jewel_infernal_cry_exerted_attacks_ignite_damage_+%_final_with_for_strength_in_radius` |
| Doedre's Elixir | Flask | Gain (1-3) Frenzy Charge on use | Offence | `local_flask_gain_frenzy_charges_on_use` |
| Doedre's Elixir | Flask | Gain (1-3) Power Charge on use | Offence | `local_flask_gain_power_charges_on_use` |
| Doppelganger Guise | Body Armour | Enemies Killed by your Hits are destroyed while Insane | Offence | `enemies_explode_on_kill_while_unhinged` |
| Dyadus | One Handed Axe | Chill Enemies for 1 second on Hit with this Weapon when in Off Hand | Offence | `local_chill_on_hit_ms_if_in_off_hand` |
| Earendel's Embrace | Sceptre | Summoned Skeletons Cover Enemies in Ash on Hit | Offence | `summoned_skeletons_cover_in_ash_on_hit_%` |
| Echoforge | Two Handed Sword | (-16-16)% reduced Attack Speed | Offence | `attack_speed_+%` |
| Echoforge | Two Handed Sword | (-40-40)% reduced Area of Effect for Attacks | Offence | `attack_area_of_effect_+%` |
| Esh's Mirror | Shield | Shocks you inflict spread to other Enemies within 1.5 metres | Offence | `gloves_shock_proliferation_radius` |
| Faminebind | Belt | Deals 50 Chaos Damage per second to Enemies within 3 metres | Offence | `local_display_aura_base_chaos_damage_to_deal_per_minute` |
| Farrul's Bite | Helmet | Critical Strikes have (10-20)% chance to Blind Enemies while you have Cat's Stealth | Offence | `%_chance_to_blind_on_critical_strike_while_you_have_cats_stealth` |
| Farrul's Fur | Body Armour | Gain up to your maximum number of Frenzy and Power Charges when you gain Cat's Stealth | Offence | `gain_maximum_frenzy_and_power_charges_when_you_gain_cats_stealth` |
| Fenumus' Toxins | Helmet | 10% chance to gain a Power Charge on hitting an Enemy affected by a Spider's Web | Offence | `chance_to_gain_power_charge_on_hitting_enemy_affected_by_spiders_web_%` |
| Fox's Fortune | Body Armour | Damage of Enemies Hitting you is Unlucky while you are on Full Life | Offence | `enemy_extra_damage_rolls_when_on_full_life` |
| Foxshade | Body Armour | Damage of Enemies Hitting you is Unlucky while you are on Full Life | Offence | `enemy_extra_damage_rolls_when_on_full_life` |
| Fragment of Eternity | Dagger | 15% chance to gain a Power Charge on Kill | Offence | `add_power_charge_on_kill_%_chance` |
| From Dust | Jewel | +1 second to Summon Skeleton Cooldown | Offence | `summon_skeletons_cooldown_modifier_ms` |
| Frozen Trail | Jewel | With at least 40 Intelligence in Radius, Frostbolt Projectiles gain 40% increased Projectile Speed per second | Offence | `local_unique_jewel_frostbolt_projectile_acceleration_with_50_int_in_radius` |
| Garb of the Ephemeral | Body Armour | Gain a Divine Charge on Hit | Offence | `gain_divine_charge_on_hit_%` |
| Garukhan's Flight | Boots | Immune to Burning Ground, Shocked Ground and Chilled Ground | Offence | `immune_to_burning_shocks_and_chilled_ground` |
| Goblinedge | Dagger | +3 seconds to Duration of Frenzy and Power Charges on Culling Strike | Offence | `frenzy_and_power_charge_add_duration_ms_on_cull` |
| Grasping Nightshade | Tincture | (20-30)% chance to inflict a Grasping Vine on Melee Weapon Hit | Offence | — |
| Grasping Nightshade | Tincture | 25% chance to Blind Enemies on Hit with Melee Weapons | Offence | — |
| Grattus Signet | Ring | Attacks inflict Unnerve on Critical Strike for 4 seconds | Offence | `attacks_inflict_unnerve_on_crit` |
| Grattus Signet | Ring | Spells inflict Intimidate on Critical Strike for 4 seconds | Offence | `spells_inflict_intimidate_on_crit` |
| Growing Agony | Jewel | With at least 40 Dexterity in Radius, Viper Strike has a 10% chance per Poison on Enemy to grant Unholy Might for 4 seconds on Hit | Offence | `local_unique_jewel_viper_strike_chance_to_gain_unholy_might_%_on_hit_per_poison_stack_on_enemy_with_50_dex_in_radius` |
| Hazardous Research | Jewel | With at least 40 Intelligence in Radius, Spark fires Projectiles in a circle | Offence | `local_unique_jewel_spark_projectiles_nova_with_40_int_in_radius` |
| Headhunter | Belt | (20-30)% increased Damage with Hits against Rare monsters | Offence | `damage_+%_vs_rare_monsters` |
| Hegemony's Era | Staff | 10% chance to gain a Power Charge if you Knock an Enemy Back with Melee Damage | Offence | `unique_add_power_charge_on_melee_knockback_%` |
| Hezmana's Bloodlust | Two Handed Axe | 25% chance to Maim on Hit | Offence | `local_maim_on_hit_%` |
| Honoured Alliance | Ring | 10% chance to Trigger Summon Spirit of Akoya on Kill | Offence | `chance_to_gain_tukohamas_embrace_%_on_kill` |
| Hyaon's Fury | One Handed Sword | 20 Life gained on Kill per Frenzy Charge | Offence | `life_gained_on_enemy_death_per_frenzy_charge` |
| Hyperboreus | Belt | Chill Enemies within 3 metres when you Focus, causing 30% reduced Action Speed | Offence | `chill_nearby_enemies_when_you_focus` |
| Icefang Orbit | Ring | Non-Chilled Enemies you Poison are Chilled | Offence | `non_chilled_enemies_you_poison_are_chilled` |
| Icefang Orbit | Ring | Poisoned Enemies you Kill with Hits Shatter | Offence | `shatter_on_kill_vs_poisoned_enemies` |
| Icetomb | Body Armour | 20% chance to Freeze Enemies for 1 second when they Hit you | Offence | `chance_to_freeze_enemies_for_1_second_when_hit_%` |
| Innsbury Edge | One Handed Sword | Attacks with this Weapon Maim on hit | Offence | `local_maim_on_hit` |
| Inya's Epiphany | Boots | 25% chance that if you would gain Power Charges, you instead gain up to | Offence | — |
| Inya's Epiphany | Boots | your maximum number of Power Charges | Offence | — |
| Jaws of Agony | Shield | 25% chance to gain a Power Charge when you Throw a Trap | Offence | `gain_power_charge_when_throwing_trap_%` |
| Jiquani's Potential | Staff | +(-1-1) to Level of all Spell Skill Gems | Offence | — |
| Kaom's Binding | Belt | Take no Burning Damage if you've stopped taking Burning Damage Recently | Offence | `take_no_fire_damage_over_time_if_stopped_taking_fire_damage_over_time_recently` |
| Kitava's Feast | Two Handed Axe | Enemies Killed by your Hits are destroyed | Offence | `enemies_explode_on_kill` |
| Kondo's Pride | Two Handed Sword | 30% chance to Blind Enemies on Critical Strike | Offence | `%_chance_to_blind_on_critical_strike` |
| Legacy of Fury | Boots | Enemy for 4 seconds, dealing 8% of the Killed Enemy's Life as Fire Damage per second | Offence | — |
| Lioneye's Vision | Body Armour | Enemy Projectiles Pierce you | Offence | `projectiles_always_pierce_you` |
| Lori's Lantern | Ring | Damage of Enemies Hitting you is Unlucky while you are on Low Life | Offence | `enemy_extra_damage_rolls_when_on_low_life` |
| Lycosidae | Shield | Adds 250 to 300 Cold Damage to Retaliation Skills | Offence | `counter_attacks_minimum_added_cold_damage`, `counter_attacks_maximum_added_cold_damage` |
| Machina Mitts | Gloves | Lose a Power Charge each second if you have not Detonated Mines Recently | Offence | `lose_power_charge_each_second_if_not_detonated_mines_recently` |
| Malachai's Loop | Shield | (20-40)% chance to gain a Power Charge on Hit | Offence | `add_power_charge_on_skill_hit_%` |
| Malachai's Loop | Shield | Lose all Power Charges on reaching Maximum Power Charges | Offence | `lose_all_power_charges_on_reaching_maximum_power_charges` |
| Malachai's Loop | Shield | Shocks you when you reach Maximum Power Charges | Offence | `shocked_for_4_seconds_on_reaching_maximum_power_charges` |
| Maligaro's Cruelty | Amulet | (12-15)% chance to gain a Power Charge on Killing an Enemy affected by fewer than 5 Poisons | Offence | `gain_power_charge_on_kill_vs_enemies_with_less_than_5_poisons_%` |
| Maligaro's Cruelty | Amulet | (25-30)% chance to gain a Frenzy Charge on Killing an Enemy affected by at least 5 Poisons | Offence | `gain_frenzy_charge_on_kill_vs_enemies_with_5+_poisons_%` |
| Maloney's Mechanism | Quiver | 5% chance to Blind Enemies on Hit with Attacks | Offence | `attacks_chance_to_blind_on_hit_%` |
| Mark of Submission | Ring | Curse Enemies with Socketed Hex Curse Gem on Hit | Offence | `local_display_curse_enemies_with_socketed_curse_on_hit_%_chance` |
| Mark of the Red Covenant | Helmet | Damage to Surrounding Targets | Offence | — |
| Maw of Mischief | Helmet | Minions are Aggressive | Offence | `minion_larger_aggro_radius` |
| Meginord's Vise | Gloves | Melee Hits with Strike Skills always Knockback | Offence | `strike_skills_knockback_on_melee_hit` |
| Meginord's Vise | Gloves | Melee Strike Skills deal Splash Damage to surrounding targets | Offence | `melee_splash` |
| Mightblood Ire | Tincture | Melee Strike Skills deal Splash Damage to surrounding targets | Offence | `melee_splash` |
| Mjolner | One Handed Mace | Socketed Lightning Spells have no Cost if Triggered | Offence | — |
| Mon'tregul's Grasp | Sceptre | Enemies Killed by Zombies' Hits Explode, dealing 50% of their Life as Fire Damage | Offence | `zombie_explode_on_kill_%_fire_damage_to_deal` |
| Moonsorrow | Wand | 10% chance to Blind Enemies on Hit | Offence | `local_chance_to_blind_on_hit_%` |
| Mutated Growth | Jewel | 10% increased Experience Gain for Corrupted Gems | Offence | `corrupted_gem_experience_gain_+%` |
| Mutewind Whispersteps | Boots | Unaffected by Chilled Ground | Offence | `unaffected_by_chilled_ground` |
| Nadir Mode | Jewel | Spells which have gained Intensity Recently lose 1 Intensity every 0.5 Seconds | Offence | `skills_lose_intensity_every_x_milliseconds_if_gained_intensity_recently` |
| Nimis | Ring | Projectiles Return to you | Offence | `projectiles_return`, `projectile_return_%_chance` |
| Nimis | Ring | Projectiles are fired in random directions | Offence | `random_projectile_direction` |
| Null and Void | Gloves | Gain Immunity to Physical Damage for 1.5 seconds on Rampage | Offence | `gain_physical_damage_immunity_on_rampage_threshold_ms` |
| Null's Inclination | Bow | Minion Spells Triggered by this Item have a 0.25 second Cooldown with 5 Uses | Offence | — |
| Null's Inclination | Bow | Trigger Socketed Minion Spells on Kill with this Weapon | Offence | — |
| Nuro's Harp | Bow | (30-50)% increased Effect of Chilled Ground | Offence | `chilled_ground_effect_+%` |
| Nuro's Harp | Bow | 15% chance to create Chilled Ground when you Freeze an Enemy | Offence | `chilled_ground_on_freeze_%_chance_for_3_seconds` |
| Oro's Sacrifice | Two Handed Sword | Gain a Frenzy Charge if an Attack Ignites an Enemy | Offence | `gain_frenzy_charge_if_attack_ignites` |
| Perquil's Toe | Amulet | Damage with Hits of Allies within 5 metres is Lucky | Offence | `local_display_nearby_allies_extra_damage_rolls` |
| Perquil's Toe | Amulet | Lightning Damage of Enemies Hitting you is Lucky | Offence | `enemies_extra_damage_rolls_with_lightning_damage` |
| Precursor's Emblem | Ring | (15-45)% chance that if you would gain Power Charges, you instead gain up to your maximum number of Power Charges | Offence | — |
| Pugilist | Jewel | 1% increased Melee Physical Damage with Unarmed Attacks per 3 Dexterity Allocated in Radius | Offence | `local_unique_jewel_unarmed_damage_+%_per_X_dex_in_radius` |
| Putrid Seed | Jewel | Grows four random Passive Skills when Anointed | Offence | — |
| Putrid Seed | Jewel | Passive Skills grown are influenced by Oils used when Anointing | Offence | — |
| Pyre | Ring | Ignited Enemies Killed by your Hits are destroyed | Offence | `ignited_enemies_explode_on_kill` |
| Redblade Band | Ring | Socketed Golem Skills have 25% chance to Taunt on Hit | Offence | `local_display_socketed_golem_chance_to_taunt_%` |
| Refuge in Isolation | Helmet | Physical Damage of Enemies Hitting you is Unlucky | Offence | `enemies_extra_damage_rolls_with_physical_damage` |
| Relic of the Cycle | Bow | Projectiles Return to you from final target | Offence | — |
| Replica Badge of the Brotherhood | Amulet | (20-25)% chance to lose a Frenzy Charge when you use a Travel Skill | Offence | `lose_a_frenzy_charge_on_travel_skill_use_%_chance` |
| Replica Earendel's Embrace | Sceptre | Raised Zombies Cover Enemies in Ash on Hit | Offence | `raised_zombies_cover_in_ash_on_hit_%` |
| Replica Headhunter | Belt | (20-30)% increased Damage with Hits against Magic monsters | Offence | `damage_+%_vs_magic_monsters` |
| Replica Kalisa's Grace | Gloves | Gain 40% increased Area of Effect for 2 seconds after Spending a total of 800 Mana | Offence | `gain_area_of_effect_+%_for_2_seconds_when_you_spend_800_mana` |
| Replica Maloney's Mechanism | Quiver | 5% chance to Blind Enemies on Hit with Attacks | Offence | `attacks_chance_to_blind_on_hit_%` |
| Replica Maloney's Mechanism | Quiver | Trigger a Socketed Bow Skill when you Cast a Spell while | Offence | — |
| Replica Maloney's Mechanism | Quiver | wielding a Bow, with a 1 second Cooldown | Offence | — |
| Replica Pacifism | Jewel | Lose a Frenzy Charge each second | Offence | `gain_X_frenzy_charges_per_second` |
| Replica Powerlessness | Jewel | Lose a Power Charge each second | Offence | `gain_X_power_charges_per_second` |
| Replica Red Trail | Boots | 50% chance for Spell Hits against you to inflict Poison | Offence | `spell_hits_against_you_inflict_poison_%` |
| Replica Red Trail | Boots | Gain a Power Charge on Hit while Poisoned | Offence | `add_power_charge_on_hit_while_poisoned_%` |
| Replica Siegebreaker | Belt | Minions have 5% chance to Maim Enemies on Hit with Attacks | Offence | `minion_maim_on_hit_%` |
| Replica Tulfall | Wand | 50% chance to gain a Power Charge when you Hit a Frozen Enemy | Offence | `gain_power_charge_on_hit_%_chance_against_frozen_enemy` |
| Replica Tulfall | Wand | Gain a Frenzy Charge on reaching Maximum Power Charges | Offence | `gain_frenzy_charge_on_reaching_maximum_power_charges` |
| Replica Tulfall | Wand | Lose all Power Charges on reaching Maximum Power Charges | Offence | `lose_all_power_charges_on_reaching_maximum_power_charges` |
| Replica Tulfall | Wand | Take 500 Cold Damage on reaching Maximum Power Charges | Offence | `self_cold_damage_on_reaching_maximum_power_charges` |
| Replica Victario's Charity | Shield | 10% chance to grant a Frenzy Charge to Allies within 4 metres on Kill | Offence | `chance_to_grant_frenzy_charge_to_nearby_allies_on_kill_%` |
| Retaliation Charm | Amulet | (10-20)% chance to Blind Enemies on Hit with Attacks | Offence | `attacks_chance_to_blind_on_hit_%` |
| Retaliation Charm | Amulet | (10-20)% chance to gain a Frenzy Charge on Hit while Blinded | Offence | `gain_frenzy_charge_on_hit_%_while_blinded` |
| Ring of Blades | Jewel | With at least 40 Dexterity in Radius, Ethereal Knives fires Projectiles in a circle | Offence | `local_unique_jewel_ethereal_knives_projectiles_nova_with_50_dex_in_radius` |
| Rive | Claw | 30% Chance to cause Bleeding Enemies to Flee on hit | Offence | `%_chance_to_cause_bleeding_enemies_to_flee_on_hit` |
| Romira's Banquet | Ring | Gain a Power Charge on Non-Critical Strike | Offence | `unique_gain_power_charge_on_non_crit` |
| Romira's Banquet | Ring | Lose all Power Charges on Critical Strike | Offence | `unique_lose_all_power_charges_on_crit` |
| Rotblood Promise | Ring | Curse Auras from Socketed Skills also affect you | Offence | `local_display_socketed_gems_curse_auras_also_affect_you` |
| Rotgut | Flask | Consumes Frenzy Charges on use | Offence | `local_flask_consumes_x_frenzy_charges_on_use` |
| Rotgut | Flask | Gain Onslaught for 3 seconds per Frenzy Charge consumed on use | Offence | `local_flask_gain_x_seconds_of_onslaught_per_frenzy_charge_consumed` |
| Sacrificial Heart | Amulet | Gain up to maximum Power Charges when you use a Vaal Skill | Offence | `gain_maximum_power_charges_on_vaal_skill_use` |
| Scaeva | One Handed Sword | (6-8)% increased Global Defences per Empty Socket | Offence | `global_defences_+%_per_empty_gem_socket_on_item` |
| Self-Flagellation | Jewel | An additional Curse can be applied to you | Offence | `number_of_additional_curses_allowed_on_self` |
| Shackles of the Wretched | Gloves | You grant (4-6) Frenzy Charges to Allies within 5 metres on Death | Offence | `grant_X_frenzy_charges_to_nearby_allies_on_death` |
| Siegebreaker | Belt | Minions have 5% chance to Taunt on Hit with Attacks | Offence | `minion_attacks_chance_to_taunt_on_hit_%` |
| Sinvicta's Mettle | Two Handed Axe | Gain a Frenzy Charge on every 50th Rampage Kill | Offence | `add_frenzy_charge_every_50_rampage_stacks` |
| Sire of Shards | Staff | Socketed Gems fire Projectiles in a circle | Offence | `local_display_socketed_gems_projectiles_nova` |
| Skin of the Lords | Body Armour | You can only Socket Corrupted Gems in this item | Offence | `local_can_only_socket_corrupted_gems` |
| Skyforth | Boots | 25% chance to gain a Power Charge on Critical Strike | Offence | `add_power_charge_on_critical_strike_%` |
| Skysunder | Two Handed Sword | Ignites you inflict with this weapon spread to other Enemies within 2.8 metres | Offence | `local_emberglow_ignite_proliferation_radius` |
| Slavedriver's Hand | Gloves | 10% chance to gain an Endurance, Frenzy or Power Charge when any | Offence | — |
| Slavedriver's Hand | Gloves | of your Traps are Triggered by an Enemy | Offence | — |
| Speaker's Wreath | Helmet | Minions' Hits can only Kill Ignited Enemies | Offence | `minions_hits_can_only_kill_ignited_enemies` |
| Steel Spirit | Jewel | With at least 40 Dexterity in Radius, each Spectral Throw Projectile gains 5% increased Damage each time it Hits | Offence | `local_unique_jewel_spectral_throw_damage_for_each_enemy_hit_with_spectral_weapon_+%_with_50_dexterity_in_radius` |
| Steelworm | Quiver | Attacks that Fire Projectiles Consume up to 1 additional Steel Shard | Offence | `steel_ammo_consumed_per_use_with_attacks_that_fire_projectiles` |
| Storm Prison | Wand | (25-35)% chance to gain a Power Charge on Kill | Offence | `add_power_charge_on_kill_%_chance` |
| Storm Secret | Ring | Herald of Thunder also creates a storm when you Shock an Enemy | Offence | `display_herald_of_thunder_storm`, `create_herald_of_thunder_storm_on_shocking_enemy` |
| Storm's Gift | Gloves | Enemies you kill are Shocked | Offence | `enemy_shock_on_kill` |
| Storm's Gift | Gloves | Shocks you inflict spread to other Enemies within 1.5 metres | Offence | `gloves_shock_proliferation_radius` |
| Stormcharger | Boots | Unaffected by Shocked Ground | Offence | `unaffected_by_shocked_ground` |
| Sudden Ignition | Jewel | Ignited Enemies Killed by your Hits are destroyed | Offence | `ignited_enemies_explode_on_kill` |
| Sunblast | Belt | Traps cannot be triggered by Enemies | Offence | `traps_cannot_be_triggered_by_enemies` |
| Sunblast | Belt | Traps from Skills are thrown randomly around targeted location | Offence | `unique_sunblast_throw_traps_in_circle_radius` |
| Survival Skills | Jewel | Flasks gain 2 Charges when you hit a Non-Unique Enemy, no more than once per second | Offence | `flasks_gain_x_charges_on_hit_once_per_second_vs_non_unique` |
| Taproot | Dagger | (15-20)% chance to Maim on Hit | Offence | `local_maim_on_hit_%` |
| Terminus Est | Two Handed Sword | Gain a Frenzy Charge on Critical Strike | Offence | `add_frenzy_charge_on_critical_strike` |
| The Blood Dance | Boots | (20-30)% chance to gain a Frenzy Charge on Kill | Offence | `add_frenzy_charge_on_kill_%_chance` |
| The Blue Dream | Jewel | also grant an equal chance to gain a Power Charge on Kill | Offence | — |
| The Brine Crown | Helmet | 15% chance to create Chilled Ground when Hit with an Attack | Offence | `chilled_ground_when_hit_with_attack_%` |
| The Crimson Storm | Bow | 50% chance to Maim Enemies on Critical Strike with Attacks | Offence | `maim_on_crit_%_with_attacks` |
| The Crimson Storm | Bow | Enemies you inflict Bleeding on grant (60-100)% increased Flask Charges | Offence | `enemies_you_bleed_grant_flask_charges_+%` |
| The Devourer of Minds | Helmet | Endurance, Frenzy and Power Charges as you | Offence | — |
| The Devourer of Minds | Helmet | Minions count as having the same number of | Offence | — |
| The Devourer of Minds | Helmet | Minions have the same maximum number of Endurance, Frenzy and Power Charges as you | Offence | `minions_have_same_maximum_num_of_charges_as_owner` |
| The Devouring Diadem | Helmet | Trigger Level 15 Feast of Flesh every 5 seconds | Offence | `local_display_trigger_level_X_feast_of_flesh_every_5_seconds` |
| The Draugur's Lantern | Shield | Draugurflames burn enemies around you for 8 seconds after you Ignite a target | Offence | `has_ghost_furnace` |
| The Eternal Struggle | Amulet | Critical Strikes inflict Malignant Madness if The Eater of Worlds is dominant | Offence | `local_inflict_malignant_madness_on_critical_strike_%_if_eater_of_worlds_dominant` |
| The Eternal Struggle | Amulet | Kill Enemies that have 15% or lower Life on Hit if The Searing Exarch is dominant | Offence | `local_kill_enemy_on_hit_if_under_15%_life_if_searing_exarch_dominant` |
| The Eternity Shroud | Body Armour | Trigger Level 20 Glimpse of Eternity when Hit | Offence | `local_display_trigger_temporal_anomaly_when_hit_%_chance` |
| The Geomantic Gyre | Staff | Has a Crucible Passive Skill Tree with only Support Passive Skills | Offence | — |
| The Gluttonous Tide | Bow | (20-40)% chance to gain a Frenzy Charge for each Enemy you hit with a Critical Strike | Offence | `gain_frenzy_charge_per_enemy_you_crit_%_chance` |
| The Gluttonous Tide | Bow | Lose all Frenzy Charges on reaching Maximum Frenzy Charges to make the next Bow Attack you perform fire that many additional Arrows | Offence | `bow_attacks_turn_frenzy_charges_into_additional_arrows` |
| The Goddess Scorned | One Handed Sword | You can only deal Damage with this Weapon or Ignite | Offence | `local_can_only_deal_damage_with_this_weapon` |
| The Goddess Unleashed | One Handed Sword | Gain Her Blessing for 3 seconds when you Ignite an Enemy | Offence | `gain_her_blessing_for_3_seconds_on_ignite_%` |
| The Green Dream | Jewel | also grant an equal chance to gain a Frenzy Charge on Kill | Offence | — |
| The Halcyon | Amulet | Freezes you inflict spread to other Enemies within 1.5 metres | Offence | `amulet_freeze_proliferation_radius` |
| The Hallowed Monarch | Helmet | On Killing a Rare monster, a random Linked Minion gains its Modifiers for 60 seconds | Offence | `link_skills_grant_random_linked_minion_rare_monster_mods_on_kill_centiseconds` |
| The Hand of Phrecia | Gloves | Linked Targets always count as in range of Non-Curse Auras from your Skills | Offence | — |
| The Hungry Loop | Ring | Can Consume 4 Uncorrupted Support Gems | Offence | — |
| The Hungry Loop | Ring | Consumes Socketed Uncorrupted Support Gems when they reach Maximum Level | Offence | — |
| The Hungry Loop | Ring | Has not Consumed any Gems | Offence | — |
| The Infinite Pursuit | Boots | Moving while Bleeding doesn't cause you to take extra Damage | Offence | `no_extra_bleed_damage_while_moving` |
| The Pandemonius | Amulet | Blind Chilled Enemies on Hit | Offence | `blind_chilled_enemies_on_hit_%` |
| The Pandemonius | Amulet | Chill Enemy for 1 second when Hit, reducing their Action Speed by 30% | Offence | `chill_enemy_when_hit_duration_ms` |
| The Queen's Hunger | Body Armour | Trigger Level 20 Bone Offering, Flesh Offering, Spirit Offering every 5 seconds in sequence | Offence | — |
| The Red Trail | Boots | Gain a Frenzy Charge on Hit while Bleeding | Offence | `gain_frenzy_charge_on_hit_while_bleeding` |
| The Sands of Time | Sceptre | Trigger level 20 Suspend in Time on Casting a Spell | Offence | `create_sand_mirage_on_contact_for_damaging_non_channel_spells` |
| The Stormheart | Staff | 50% chance to Shock Chilled Enemies | Offence | `chance_to_shock_chilled_enemies_%` |
| The Sundered Will | Ring | Cannot roll Modifiers of Non-Chaos Damage Types | Offence | `breach_ring_chayula_implicit` |
| The Untouched Soul | Amulet | Players have +225 to Accuracy Rating for each Empty Green Socket on any Equipped Item | Offence | `accuracy_rating_+_per_empty_green_socket` |
| The Warden's Brand | Ring | 15% chance to gain a Frenzy Charge when you Stun an Enemy | Offence | `chance_to_gain_frenzy_charge_on_stun_%` |
| The Will of Esh | Ring | Cannot roll Modifiers of Non-Lightning Damage Types | Offence | `breach_ring_esh_implicit` |
| The Will of Tul | Ring | Cannot roll Modifiers of Non-Cold Damage Types | Offence | `breach_ring_tul_implicit` |
| The Will of Uul-Netol | Ring | Cannot roll Modifiers of Non-Physical Damage Types | Offence | `breach_ring_uulnetol_implicit` |
| The Will of Xoph | Ring | Cannot roll Modifiers of Non-Fire Damage Types | Offence | `breach_ring_xoph_implicit` |
| Thunder of the Dawn | Two Handed Sword | When you Kill a Shocked Enemy, inflict an equivalent Shock on each nearby Enemy | Offence | — |
| Timeclasp | Ring | (-20-20)% reduced Skill Effect Duration | Offence | `skill_effect_duration_+%` |
| Timetwist | Ring | (-10-10)% reduced Skill Effect Duration | Offence | `skill_effect_duration_+%` |
| Tinkerskin | Body Armour | 15% chance to gain a Frenzy Charge when your Trap is triggered by an Enemy | Offence | `%_chance_to_gain_frenzy_charge_on_trap_triggered_by_an_enemy` |
| Touch of Anguish | Claw | 20% chance to gain a Frenzy Charge on Killing a Frozen Enemy | Offence | `chance_to_gain_frenzy_charge_on_killing_frozen_enemy_%` |
| Tremor Rod | Staff | Mines can be Detonated an additional time | Offence | `mine_extra_uses` |
| Tulborn | Wand | Gain a Power Charge on Killing a Frozen Enemy | Offence | `chance_to_gain_power_charge_on_killing_frozen_enemy_%` |
| Tulfall | Wand | Gain a Frenzy Charge on reaching Maximum Power Charges | Offence | `gain_frenzy_charge_on_reaching_maximum_power_charges` |
| Tulfall | Wand | Gain a Power Charge on Killing a Frozen Enemy | Offence | `chance_to_gain_power_charge_on_killing_frozen_enemy_%` |
| Tulfall | Wand | Lose all Power Charges on reaching Maximum Power Charges | Offence | `lose_all_power_charges_on_reaching_maximum_power_charges` |
| Unholy Accomplice | Belt | Pact Skills grant Boons instead of Afflictions | Offence | `gain_boons_instead_of_afflictions_when_using_a_pact_skill` |
| Unlight Extant | Wand | Cannot Inflict Wither on targets that are not on Full Life | Offence | `can_only_inflict_wither_against_full_life_enemies` |
| Unstable Payload | Jewel | (8-12)% Chance for Traps to Trigger an additional time | Offence | `trap_%_chance_to_trigger_twice` |
| Usurper's Penance | Helmet | (20-30)% chance to gain a Frenzy Charge on Critical Strike at Close Range | Offence | `gain_frenzy_charge_on_critical_strike_at_close_range_%` |
| Uul-Netol's Embrace | Two Handed Axe | 25% chance to Maim on Hit | Offence | `local_maim_on_hit_%` |
| Uul-Netol's Kiss | Two Handed Axe | 25% chance to Maim on Hit | Offence | `local_maim_on_hit_%` |
| Uul-Netol's Kiss | Two Handed Axe | Exerted Attacks Knock Enemies Back on Hit | Offence | `exerted_attack_knockback_chance_%` |
| Venopuncture | Ring | Bleeding Enemies you Kill with Hits Shatter | Offence | `shatter_on_kill_vs_bleeding_enemies` |
| Venopuncture | Ring | Non-Chilled Enemies you inflict Bleeding on are Chilled | Offence | `non_chilled_enemies_you_bleed_are_chilled` |
| Ventor's Gamble | Ring | (-15-15)% reduced Mana Reservation Efficiency of Skills | Offence | `base_mana_reservation_efficiency_+%` |
| Victario's Acuity | Amulet | 10% chance to gain a Frenzy Charge on Kill | Offence | `add_frenzy_charge_on_kill_%_chance` |
| Victario's Acuity | Amulet | 10% chance to gain a Power Charge on Kill | Offence | `add_power_charge_on_kill_%_chance` |
| Victario's Charity | Shield | 10% chance to grant a Power Charge to Allies within 4 metres on Kill | Offence | `chance_to_grant_power_charge_to_nearby_allies_on_kill_%` |
| Victario's Charity | Shield | 5% chance to grant a Frenzy Charge to Allies within 4 metres on Hit | Offence | `chance_to_grant_frenzy_charge_to_nearby_allies_on_hit_%` |
| Viridi's Veil | Helmet | Damage of Enemies Hitting you is Unlucky while you have a Magic Ring Equipped | Offence | `enemy_extra_damage_rolls_if_magic_ring_equipped` |
| Voll's Protector | Body Armour | Gain a Power Charge for each Enemy you hit with a Critical Strike | Offence | `gain_power_charge_per_enemy_you_crit` |
| Volley Fire | Jewel | With at least 40 Dexterity in Radius, Barrage fires an additional 6 projectiles simultaneously on the first and final attacks | Offence | `local_unique_jewel_barrage_final_volley_fires_x_additional_projectiles_simultaneously_with_50_dex_in_radius` |
| Vorana's March | Boots | Summoned Arbalists have (20-30)% chance to Intimidate for 4 seconds on Hit | Offence | `summon_arbalist_chance_to_intimidate_for_4_seconds_on_hit_%` |
| Warrior's Legacy | Ring | Strike Skills also target the previous location they were used | Offence | `melee_strike_skill_strike_previous_location` |
| Wildfire | Jewel | With at least 40 Strength in Radius, Molten Strike Projectiles Chain on impacting ground | Offence | `local_jewel_molten_strike_projectiles_chain_when_impacting_ground_with_40_str_in_radius` |
| Wildfire Phloem | Tincture | (15-25)% chance to refresh Ignite Duration on Melee Weapon Hit | Offence | — |
| Wildfire Phloem | Tincture | Cover Full Life Enemies in Ash for (4-10) seconds on Melee Weapon Hit | Offence | — |
| Willclash | Helmet | Gain a Power Charge every Second if you haven't lost Power Charges Recently | Offence | `gain_power_charge_per_second_if_have_not_lost_power_charge_recently` |
| Winter Burial | Jewel | Cold-only Splash Damage to surrounding targets | Offence | — |
| Winter's Bounty | Jewel | With at least 40 Intelligence in Radius, Cold Snap grants Power Charges instead of Frenzy Charges when Enemies die in its Area | Offence | — |
| Winter's Bounty | Jewel | With at least 40 Intelligence in Radius, Cold Snap's Cooldown can be bypassed by Power Charges instead of Frenzy Charges | Offence | — |
| Woespike | Ring | (20-30)% chance on Melee Hit for the Strongest Impale on target to last for 1 additional Hit | Offence | `impales_do_not_consume_hit_strongest_impale_on_melee_hit_%_chance` |
| Worldcarver | Gloves | 3% increased Attack Speed for each Map Item Modifier affecting the Area | Offence | `attack_speed_+%_per_explicit_map_mod_affecting_area` |
| Worldcarver | Gloves | 6% increased Attack Damage for each Map Item Modifier affecting the Area | Offence | `attack_damage_+%_per_explicit_map_mod_affecting_area` |
| Worldcarver | Gloves | Trigger Level 20 Arcane Wake after Spending a total of 200 Mana | Offence | `display_trigger_arcane_wake_after_spending_200_mana_%_chance` |
| Ylfeban's Trickery | Helmet | Curse Enemies which Hit you with a random Hex, ignoring Curse Limit | Offence | `random_curse_when_hit_%_ignoring_curse_limit` |
| Afarud Ritual | Necromantic | Damageable Minions deal 30% increased Damage for each second they have been alive, | Offence | — |
| Afarud Ritual | Necromantic | Damageable Minions take 5% increased Damage for each second they have been alive, | Offence | — |
| Aggravate Bleeding On Critical Strike Chance | Normal | 25% chance to Aggravate Bleeding on targets you Critically Strike with Attacks | Offence | `aggravate_bleeding_on_attack_crit_chance_%` |
| Aggravate Bleeding On Critical Strike Chance | Normal | 25% chance to Aggravate Bleeding on targets you Critically Strike with Attacks | Offence | `aggravate_bleeding_on_attack_crit_chance_%` |
| Ancestral Fury | Berserker | Strike Skills also target the previous location they were used | Offence | `melee_strike_skill_strike_previous_location` |
| Ancestral Guidance | Notable | Totems' Action Speed cannot be modified to below Base Value | Offence | `totems_action_speed_cannot_be_modified_below_base` |
| Ancestral Reach | Notable | 25% increased Totem Placement range | Offence | `totem_placement_range_+%` |
| Arsenal of Vengeance | Keystone | Damaging Retaliation Skills become Usable every sixth Hit from Enemies instead | Offence | — |
| Assassin | Ascendant | 10% chance to gain a Power Charge on Critical Strike | Offence | `add_power_charge_on_critical_strike_%` |
| Avatar of the Wilds | Raider | Gain 1 Unbound Fury when you inflict an Elemental Ailment with a Hit on an Enemy, no more than once every 0.2 seconds for each type of Ailment | Offence | — |
| Avidity | Deadeye | Gain a Frenzy Charge each second while Moving | Offence | `gain_a_frenzy_charge_every_X_seconds_while_moving` |
| Awe and Terror | Notable | Enemies Killed near your Banner have 20% chance to Explode, dealing a tenth of their Life as Physical Damage | Offence | `banner_affected_enemies_explode_for_10%_life_as_physical_on_kill_chance_%` |
| Bestowed Knighthood | Luminary | Your Mercenary Taunts on Hit | Offence | `permanenet_mercenary_chance_to_taunt_on_hit_%` |
| Bestowed Knighthood | Luminary | Your Mercenary has 50% increased effect of Non-Curse Auras from Skills | Offence | `permanenet_mercenary_non_curse_aura_effect_+%` |
| Blackflame | Reliquarian | Withered does not expire on Enemies Ignited by you | Offence | `enemies_you_ignite_wither_does_not_expire` |
| Blast-Freeze | Notable | Freezes you inflict spread to other Enemies within 1.2 metres | Offence | `amulet_freeze_proliferation_radius` |
| Blessed Rebirth | Notable | Minions created Recently cannot be Damaged | Offence | `minion_summoned_recently_cannot_be_damaged` |
| Blind Chance | Normal | 10% chance to Blind Enemies on Hit with Attacks | Offence | `attacks_chance_to_blind_on_hit_%` |
| Bloodletting | Notable | 10% chance to Aggravate Bleeding on targets you Hit with Attacks | Offence | `base_aggravate_bleeding_on_attack_hit_chance_%` |
| Brine Rot | Brinerot | Triggers Drowning Domain when Allocated | Offence | `local_display_trigger_brine_rot_aura_on_gain_skill` |
| Calculated Risk | Saboteur | Damage of Enemies Hitting you is Unlucky | Offence | `base_enemy_extra_damage_rolls` |
| Capacitor | Notable | Unaffected by Shocked Ground | Offence | `unaffected_by_shocked_ground` |
| Cauterisation | Notable | Ignited enemies cannot Ignite you | Offence | `cannot_be_ignited_by_ignited_enemies` |
| Chain Reaction | Saboteur | When your Traps Trigger, your Traps within 2 metres also Trigger | Offence | `nearby_traps_within_x_units_also_trigger_on_triggering_trap` |
| Champion | Ascendant | Taunt on Hit | Offence | `chance_to_taunt_on_hit_%` |
| Chance for Extra Fork Projectile | Normal | Projectiles have 25% chance for an additional Projectile when Forking | Offence | `chance_to_fork_extra_projectile_%` |
| Chaos Damage and Withered Expiry Rate | Normal | Withered you Inflict expires 10% slower | Offence | `wither_expire_speed_+%` |
| Chaos Damage and Withered Expiry Rate | Normal | Withered you Inflict expires 10% slower | Offence | `wither_expire_speed_+%` |
| Chieftain | Ascendant | 20% chance to Cover Rare or Unique Enemies in Ash for 10 Seconds on Hit | Offence | `apply_covered_in_ash_to_attacker_on_hit_%_vs_rare_or_unique_enemy` |
| Chip Away | Notable | Brand Recall grants 20% increased Brand Attachment range to recalled Brands | Offence | `recall_sigil_target_search_range_+%` |
| Cleaving | Notable | 15% chance to Intimidate Enemies for 4 seconds on Hit with Attacks | Offence | `attacks_intimidate_on_hit_%` |
| Clever Construction | Notable | 10% Chance for Traps to Trigger an additional time | Offence | `trap_%_chance_to_trigger_twice` |
| Concussive Force | Notable | Hits Stun as though dealing 50% more Melee Fire Damage | Offence | `passive_skill_hits_stun_as_if_dealing_melee_fire_damage_+%_final` |
| Concussive Force | Notable | Ignites from Stunning Melee Hits deal 20% more Damage | Offence | `passive_skill_ignites_from_stunning_melee_hits_deal_damage_+%_final` |
| Conduit | Keystone | Share Endurance, Frenzy and Power Charges with nearby party members | Offence | — |
| Conjoined Spire | Abyssal | All other Summoned Totems die when you Summon a Totem | Offence | `maximum_1_totem_at_a_time` |
| Cremator | Notable | Ignited Enemies Killed by your Hits are destroyed | Offence | `ignited_enemies_explode_on_kill` |
| Cruel Retort | Notable | Every fourth Retaliation Skill you use always Critically Strikes | Offence | `every_fourth_retaliation_used_is_a_critical_strike` |
| Cryogenesis | Breachlord | Elemental Hit's Added Damage cannot be replaced this way | Offence | `display_added_damage_type_replacement_no_elemental_hit` |
| Dazzling Strikes | Notable | 20% chance to Blind Enemies on Hit with Attacks | Offence | `attacks_chance_to_blind_on_hit_%` |
| Deadeye | Ascendant | Gain a Frenzy Charge every 3 seconds while Moving | Offence | `gain_a_frenzy_charge_every_X_seconds_while_moving` |
| Defiant Stand | Notable | Gain 3 Frenzy Charges when you consume maximum Valour to place a Banner | Offence | `banner_gain_X_frenzy_charges_when_placed_with_max_resources` |
| Defiled Forces | Notable | Refresh Duration of Chill and Shock on Enemies you Curse | Offence | `refresh_duration_of_shock_chill_ignite_on_enemy_when_cursing_enemy` |
| Defy Pain | Berserker | more than once every 0.3 seconds | Offence | — |
| Deliberate Brutality | Notable | Impales you inflict gain 50% increased Effect once 1 second of Duration has expired | Offence | `impale_effect_+%_for_impales_past_1000_millisecond` |
| Demolitions Specialist | Saboteur | Mines Hinder Enemies within 3 metres for 2 seconds when they Land | Offence | `mines_hinder_nearby_enemies_for_x_ms_on_arming` |
| Devastating Devices | Notable | 10% chance to gain a Power Charge when your Mine is Detonated targeting an Enemy | Offence | `%_chance_to_gain_power_charge_on_mine_detonated_targeting_an_enemy` |
| Disciple of the Forbidden | Notable | 8% chance to gain a Power Charge on Kill | Offence | `add_power_charge_on_kill_%_chance` |
| Disciple of the Slaughter | Notable | 8% chance to gain a Frenzy Charge on Kill | Offence | `add_frenzy_charge_on_kill_%_chance` |
| Dismembering | Notable | 20% chance to Maim Enemies on Critical Strike with Attacks | Offence | `maim_on_crit_%_with_attacks` |
| Disorienting Wounds | Notable | 25% chance to Blind with Hits against Bleeding Enemies | Offence | `global_chance_to_blind_on_hit_%_vs_bleeding_enemies` |
| Drive the Destruction | Notable | Attacks have 10% chance to Maim on Hit | Offence | `maim_on_hit_%` |
| Elder Power | Notable | 10% chance to gain a Power Charge on Kill | Offence | `add_power_charge_on_kill_%_chance` |
| Expert Sabotage | Notable | Mines have 20% increased Detonation Speed | Offence | `mine_detonation_speed_+%` |
| Fan the Flames | Notable | Ignites you inflict spread to other Enemies within a Radius of 1.5 metres | Offence | `spread_ignite_to_nearby_enemies` |
| Far Shot | Deadeye | Projectile Barrages have no spread | Offence | `no_barrage_projectile_spread` |
| Field Medicine | Notable | Life Flasks gain a Charge when you hit an Enemy, no more than once each second | Offence | `life_flasks_gain_a_charge_on_hit_once_per_second` |
| Fingers of Frost | Notable | Enemies Become Chilled as they Unfreeze, causing 30% reduced Action Speed | Offence | `enemies_chill_as_unfrozen` |
| Forbidden Power | Occultist | Gain a Power Charge after Spending a total of 200 Mana | Offence | `local_display_gain_power_charge_on_spending_mana` |
| Forking Angle | Normal | 50% increased Projectile Fork angle | Offence | `forking_angle_+%` |
| Forking Angle | Normal | 50% reduced Projectile Fork angle | Offence | `forking_angle_+%` |
| Foulborn Tremor Rod | Reliquarian | Mines can be Detonated an additional time | Offence | `mine_extra_uses` |
| Frigid Wake | Occultist | Every 4 seconds, 50% chance to Freeze Non-Frozen Enemies within 6 metres for 0.4 seconds | Offence | `every_4_seconds_%_chance_freeze_non_frozen_enemies_for_300ms` |
| Gladiator | Ascendant | 25% chance to Aggravate Bleeding on targets you Hit with Attacks | Offence | `base_aggravate_bleeding_on_attack_hit_chance_%` |
| Harpooner | Notable | 30% increased Effect of Impales you inflict with Two Handed Weapons on Non-Impaled Enemies | Offence | `impale_effect_+%_for_impales_inflicted_by_two_handed_weapons_on_non_impaled_enemies` |
| Hibernator | Notable | Unaffected by Chilled Ground | Offence | `unaffected_by_chilled_ground` |
| High Explosives | Notable | 15% chance to gain a Power Charge when your Trap is triggered by an Enemy | Offence | `%_chance_to_gain_power_charge_on_trap_triggered_by_an_enemy` |
| Hollow Effigy | Notable | Your Offering Skills do not require a Corpse | Offence | `offering_skills_do_not_require_corpses` |
| Hulking Corpses | Notable | Raised Zombies have 5% chance to Taunt Enemies on Hit | Offence | `raised_zombie_%_chance_to_taunt` |
| Indomitable Army | Notable | Moving while Bleeding doesn't cause Minions to take extra Damage | Offence | `minion_no_extra_bleed_damage_while_moving` |
| Insatiable Killer | Notable | 5% chance to gain a Frenzy Charge on Kill while Dual Wielding | Offence | `add_frenzy_charge_on_kill_%_chance_while_dual_wielding` |
| Jagged Technique | Gladiator | Bleeding you inflict is Aggravated | Offence | `aggravate_inflicted_bleeding` |
| Last Rites | Notable | Cursed Enemies you Kill are destroyed | Offence | `cursed_enemies_are_exorcised_on_kill` |
| Legendary Arms | Luminary | Your Mercenary and their Minions deal 8% more Damage for | Offence | — |
| Lesson of the Seasons | Raider | Lose 1 Bark when Hit by Enemy Spell Damage | Offence | `lose_X_bark_on_enemy_spell_hit` |
| Lethe Shade | Keystone | Take 50% less Damage over Time if you've started taking Damage over Time in the past second | Offence | — |
| Liquid Inspiration | Notable | 25% chance to gain a Power Charge when you use a Mana Flask | Offence | `gain_power_charge_on_mana_flask_use_%_chance` |
| Master Distiller | Pathfinder | Grant bonuses to Non-Channelling Skills you use by consuming 3 Charges from a Flask of | Offence | — |
| Master Sapper | Notable | 15% chance to gain a Frenzy Charge when your Trap is triggered by an Enemy | Offence | `%_chance_to_gain_frenzy_charge_on_trap_triggered_by_an_enemy` |
| Master Toxicist | Pathfinder | When you kill a Poisoned Enemy during any Flask Effect, Enemies within 1.5 metres are Poisoned | Offence | `unique_spread_poison_to_nearby_enemies_during_flask_effect` |
| Measured Retaliation | Gladiator | 50% chance for used Retaliation Skills to remain Usable and not consume a Cooldown Use | Offence | `retaliation_skill_keep_use_requirement_and_prevent_cooldown_on_use_chance_%` |
| Measured Retaliation | Gladiator | Retaliation Skills become Usable for an additional 2 seconds | Offence | `retaliation_skill_additional_use_window_duration_ms` |
| Mercenary Damage, Light Radius | Luminary | Your Mercenary and their Minions deal 15% increased Damage | Offence | `permanenet_mercenary_damage_+%_and_minion_damage_+%` |
| Mine Detonation Speed | Normal | Mines have 20% increased Detonation Speed | Offence | `mine_detonation_speed_+%` |
| Mine Detonation Speed | Normal | Mines have 20% increased Detonation Speed | Offence | `mine_detonation_speed_+%` |
| Mob Mentality | Notable | Warcries have 5% Chance to grant an Endurance, Frenzy or Power Charge per Power | Offence | `warcry_chance_to_gain_frenzy_power_endurance_charge_%_per_power` |
| Nature's Concoction | Notable | Enemy with a Melee Weapon, no more than once every second | Offence | — |
| Necromantic Aegis | Keystone | All bonuses from an Equipped Shield apply to your Minions instead of you | Offence | `minions_get_shield_stats_instead_of_you` |
| No Forgiveness | Notable | 20% chance for used Retaliation Skills to remain Usable and not consume a Cooldown Use | Offence | `retaliation_skill_keep_use_requirement_and_prevent_cooldown_on_use_chance_%` |
| Oath of Fealty | Luminary | Link Skills have infinite Attachment Duration | Offence | `link_skill_have_infinite_attachment_duration` |
| Oath of Winter | Raider | Enemies you Freeze remain Frozen for at least 2 seconds | Offence | `freeze_minimum_duration_X_ms` |
| Pain Forger | Notable | 10% chance to gain a Power Charge when you Stun with Melee Damage | Offence | `chance_to_gain_power_charge_on_melee_stun_%` |
| Perfect Crime | Saboteur | Grants Level 20 Summon Triggerbots | Offence | — |
| Prepared Response | Notable | Retaliation Skills become Usable for 30% longer | Offence | `retaliation_use_window_duration_+%` |
| Priest of Yaomac | Trialmaster | Vaal Skills have 20% chance to regain consumed Souls when used | Offence | `vaal_skill_soul_refund_chance_%` |
| Prolonged Servitude | Catarina | Minions cannot be Killed, but die 6 seconds after being reduced to 1 Life | Offence | `minions_cannot_be_killed_but_die_x_seconds_after_reaching_1_life` |
| Pure Guile | Notable | 5% chance to Blind Enemies on Hit | Offence | `local_chance_to_blind_on_hit_%` |
| Remarkable | Notable | Skills which create Brands have 35% chance to create an additional Brand | Offence | `create_additional_brand_%_chance` |
| Retaliation Skill Usable Duration | Normal | Retaliation Skills become Usable for 20% longer | Offence | `retaliation_use_window_duration_+%` |
| Retaliation Skill Usable Duration | Normal | Retaliation Skills become Usable for 20% longer | Offence | `retaliation_use_window_duration_+%` |
| Saboteur | Ascendant | 25% chance to Blind Enemies on Hit | Offence | `local_chance_to_blind_on_hit_%` |
| Seeker Runes | Notable | Unattached Brands gain 20% increased Brand Attachment Range per | Offence | — |
| Selective Precision | Notable | First and Final shots of Barrage sequences fire Projectiles that Return to you | Offence | `first_and_final_barrage_projectiles_return` |
| Shifting Shadow | Notable | 10% chance to Blind Enemies on Hit | Offence | `local_chance_to_blind_on_hit_%` |
| Shrapnel Specialist | Saboteur | Projectiles are fired in random directions | Offence | `random_projectile_direction` |
| Shrapnel Specialist | Saboteur | Projectiles have 50% chance to Return to you | Offence | `projectiles_return`, `projectile_return_%_chance` |
| Shrieking Bolts | Notable | 10% chance to Taunt Enemies on Projectile Hit | Offence | `taunt_on_projectile_hit_chance_%` |
| Sione's Ambition | Notable | Strike Skills which target additional Enemies can do so from 40% further away | Offence | `extra_target_targeting_distance_+%` |
| Smite the Weak | Notable | Attacks have 10% chance to Maim on Hit | Offence | `maim_on_hit_%` |
| Snaring Spirits | Notable | Totems Hinder Enemies within 3 metres of them when Summoned | Offence | `totem_hinder_nearby_enemies_when_summoned_with_25%_reduced_movement_speed` |
| Split Shot | Notable | Projectiles have 50% chance for an additional Projectile when Forking | Offence | `chance_to_fork_extra_projectile_%` |
| Stormrider | Notable | 10% chance to gain a Power Charge when you Shock a Chilled Enemy | Offence | `chance_to_grant_power_charge_on_shocking_chilled_enemy_%` |
| The Crustacean's Call | Reliquarian | Skills Supported by Spell Totem are Crab Totems | Offence | `spell_totems_are_crab_totems` |
| The Draugur's Lantern | Reliquarian | Draugurflames burn enemies around you for 8 seconds after you Ignite a target | Offence | `has_ghost_furnace` |
| The Impaler | Keystone | For 5 seconds after you Impale Enemies, they cannot be Impaled again, and Impales cannot be Called from them | Offence | — |
| The Impaler | Keystone | Inflict 5 additional Impales on Enemies you Impale | Offence | — |
| The Impaler | Keystone | When your Hits Impale Enemies, also Impale other Enemies near them | Offence | — |
| Thunderstruck | Notable | Your Critical Strikes Knock Back Shocked Enemies | Offence | `critical_strikes_always_knockback_shocked_enemies` |
| Tide Caller | Brinerot | Trigger Level 20 Surging Torrent when you cast an Elemental Spell | Offence | `local_display_trigger_brine_torrent` |
| Touch of Cruelty | Notable | Chaos Spells have 10% chance to Hinder Enemies on Hit | Offence | `chaos_skill_chance_to_hinder_on_hit_%` |
| Tribal Fury | Notable | Melee Strike Skills deal Splash Damage to surrounding targets | Offence | `melee_splash` |
| Unstable Infusion | Assassin | 15% chance to gain a Power Charge on Critical Strike | Offence | `add_power_charge_on_critical_strike_%` |
| Unstable Infusion | Assassin | 30% chance to gain a Power Charge on Non-Critical Strike | Offence | `gain_power_charge_on_non_critical_strike_%` |
| Unwaveringly Evil | Notable | Chaos Skills ignore interruption from Stuns | Offence | `cannot_be_stunned_while_using_chaos_skill` |
| Vengeant Cascade | Notable | Returning Projectiles have 150% increased Speed | Offence | `returned_projectile_speed_+%` |
| Vinespike Cordial | Notable | Inflict a Grasping Vine on Hit against Enemies with fewer than | Offence | — |
| Volatile Mines | Notable | Mines have 30% increased Detonation Speed | Offence | `mine_detonation_speed_+%` |
| Wind-up | Notable | 10% chance to gain a Power Charge on Non-Critical Strike with a Claw or Dagger | Offence | `power_charge_on_non_critical_strike_%_chance_with_claws_daggers` |
| Worthy Foe | Champion | Taunt on Hit | Offence | `chance_to_taunt_on_hit_%` |
| Wrapped in Flame | Notable | 5% chance to Cover Enemies in Ash on Hit while you are Burning | Offence | `cover_in_ash_on_hit_%_while_you_are_burning` |

## Unsupported · Defence (282)

| Source | Where | Line | Impact | Game stat id |
|---|---|---|---|---|
| Akoya's Gaze | Helmet | Life Leech from Exerted Attacks is instant | Defence | `life_leech_is_instant_for_exerted_attacks` |
| Ambu's Charge | Body Armour | Gain up to maximum Endurance Charges when you take a Critical Strike | Defence | `gain_maximum_endurance_charges_when_crit_chance_%` |
| Ambu's Charge | Body Armour | Your party members within 6 metres maximum Endurance Charges is equal to yours | Defence | `nearby_party_members_max_endurance_charges_is_equal_to_yours` |
| Annihilation's Approach | Boots | Lose Adrenaline when you cease to be Flame-Touched | Defence | `lose_adrenaline_on_losing_flame_touched` |
| Apep's Rage | Wand | Lose 40 Mana when you use a Skill | Defence | `lose_x_mana_when_you_use_skill` |
| Apep's Slumber | Shield | +25% chance to be Poisoned | Defence | `chance_to_be_poisoned_%` |
| Apep's Supremacy | Shield | +25% chance to be Poisoned | Defence | `chance_to_be_poisoned_%` |
| Apep's Supremacy | Shield | You take Chaos Damage instead of Physical Damage from Bleeding | Defence | `bleeding_damage_on_self_converted_to_chaos` |
| Atziri's Mirror | Shield | 50% reduced Duration of Curses on you | Defence | `self_curse_duration_+%` |
| Auxium | Belt | Chill Effect and Freeze Duration on you are based on 100% of Energy Shield | Defence | `chill_and_freeze_duration_based_on_%_energy_shield` |
| Bino's Kitchen Knife | Dagger | Allies Regenerate 400 Life per second for the Poison's duration if within 3 metres | Defence | — |
| Blasphemer's Grasp | Gloves | Remove an Ailment when you use a Flask if all Equipped Items are Elder Items | Defence | `remove_random_ailment_on_flask_use_if_all_equipped_items_are_elder` |
| Blood Price | Helmet | Enemy Monsters within 3 metres have at least 8% of Life Reserved | Defence | `local_display_nearby_enemy_life_reserved_by_stat_%` |
| Blood of the Karui | Flask | Recover Full Life at the end of the Effect | Defence | `local_unique_flask_recover_%_maximum_life_when_effect_reaches_duration` |
| Bloodnotch | Jewel | (20-30)% of Damage taken from Stunning Hits is Recovered as Life | Defence | `damage_taken_%_recovered_as_life_from_stunning_hits` |
| Cadigan's Authority | Sceptre | You cannot have more than 2 Summoned Totems of the same type | Defence | `maximum_2_of_same_totem` |
| Call of the Void | Ring | All Damage Taken from Hits can Chill you | Defence | `all_damage_taken_can_chill` |
| Callinellus Malleus | One Handed Mace | (15-25)% reduced Enemy Stun Threshold with this Weapon | Defence | `local_stun_threshold_reduction_+%` |
| Ceaseless Feast | Gloves | (20-30)% chance to gain a Frenzy Charge on Hitting an Enemy with no Evasion Rating | Defence | `frenzy_charge_on_hit_%_vs_no_evasion_rating` |
| Ceaseless Feast | Gloves | (20-30)% chance to gain an Endurance Charge on Hitting an Enemy with no Armour | Defence | `endurance_charge_on_hit_%_vs_no_armour` |
| Chains of Command | Body Armour | You cannot have Non-Animated, Non-Manifested Minions | Defence | `you_cannot_have_non_animated_minions` |
| Chains of Emancipation | Belt | Enemy Hits inflict Temporal Chains on you | Defence | `enemies_that_hit_you_inflict_temporal_chains` |
| Chalice of Horrors | Shield | 100% Chance to Cause Monster to Flee on Block | Defence | `block_causes_monster_flee_%` |
| Corrupted Energy | Jewel | With 5 Corrupted Items Equipped: 50% of Chaos Damage taken does not bypass Energy Shield, and 50% of Physical Damage taken bypasses Energy Shield | Defence | `half_physical_bypasses_es_half_chaos_damages_es_when_X_corrupted_items_equipped` |
| Coruscating Elixir | Flask | Removed life is Regenerated as Energy Shield over 2 seconds | Defence | — |
| Coruscating Elixir | Flask | Removes all but one Life on use | Defence | — |
| Craiceann's Tracks | Boots | You only lose (5-7) Crab Barriers when you take Physical Damage from a Hit | Defence | `number_of_crab_charges_lost_when_hit` |
| Daresso's Defiance | Body Armour | You gain Onslaught for 5 seconds per Endurance Charge when Hit | Defence | `unique_gain_onslaught_when_hit_duration_ms_per_endurance_charge` |
| Daresso's Defiance | Body Armour | You gain an Endurance Charge on Kill | Defence | `add_endurance_charge_on_kill` |
| Daresso's Defiance | Body Armour | You lose all Endurance Charges when Hit | Defence | `unique_lose_all_endurance_charges_when_hit` |
| Dawnbreaker | Shield | -1% Chance to Block Attack Damage for every 200 Fire Damage taken from Hits Recently | Defence | `attack_block_%_per_200_fire_hit_damage_taken_recently` |
| Demon Stitcher | Gloves | Sacrifice (5-25)% of Life to gain that much Energy Shield when you Cast a Spell | Defence | `sacrifice_%_maximum_life_to_gain_as_es_on_spell_cast` |
| Dissolution of the Flesh | Jewel | until you take no Damage to Life for 2 seconds | Defence | — |
| Doedre's Elixir | Flask | Gain (1-3) Endurance Charge on use | Defence | `local_flask_gain_endurance_charges_on_use` |
| Doedre's Elixir | Flask | Removes 80% of your maximum Energy Shield on use | Defence | `local_flask_removes_%_maximum_energy_shield_on_use` |
| Doedre's Elixir | Flask | You take 50% of your maximum Life as Chaos Damage on use | Defence | `local_flask_deals_%_maximum_life_as_chaos_damage_on_use` |
| Doedre's Tongue | Amulet | Cursed Enemies cannot inflict Elemental Ailments on You | Defence | `cannot_receive_elemental_ailments_from_cursed_enemies` |
| Dreadmaidens' Sacrament | Flask | Removes (10-20)% of Life when Used | Defence | `local_unique_flask_instantly_removes_%_maximum_life` |
| Echoforge | Two Handed Sword | +(-200-200) to maximum Life | Defence | — |
| Elixir of the Unbroken Circle | Flask | Gain 1 Endurance Charge per Second during Effect | Defence | `local_flask_gain_endurance_charge_per_second_during_flask_effect` |
| Elixir of the Unbroken Circle | Flask | Lose all Endurance Charges on use | Defence | — |
| Elixir of the Unbroken Circle | Flask | Recover 4% of Life per Endurance Charge on use | Defence | — |
| Elixir of the Unbroken Circle | Flask | Restores Ward on use | Defence | `local_flask_restore_ward` |
| Eternal Damnation | Amulet | +(-13-13)% to Chaos Resistance | Defence | — |
| Flesh and Spirit | Gloves | Recover 20% of Life on Rampage | Defence | `recover_%_maximum_life_on_rampage_threshold` |
| Fleshcrafter | Body Armour | Minions Convert 2% of their Maximum Life to Maximum Energy Shield per 1% Chaos Resistance they have | Defence | — |
| Font of Thunder | Shield | +50% chance to be Shocked | Defence | `chance_to_be_shocked_%` |
| Forbidden Taste | Flask | Recover (75-100)% of Life on use | Defence | `local_unique_flask_instantly_recovers_%_maximum_life` |
| Hale Negator | Helmet | Recover (2-3)% of Energy Shield when you lose a Spirit Charge | Defence | `gain_%_es_when_spirit_charge_expires_or_consumed` |
| Hale Negator | Helmet | Recover (2-3)% of Life when you lose a Spirit Charge | Defence | `gain_%_life_when_spirit_charge_expires_or_consumed` |
| Haunting Memories | Amulet | (50-100)% of Suppressed Spell Damage taken Recouped as Energy Shield | Defence | `suppressed_spell_damage_taken_%_recouped_as_es` |
| Haunting Memories | Amulet | (50-100)% of Suppressed Spell Damage taken bypasses Energy Shield | Defence | `suppressed_spell_damage_bypass_energy_shield_%` |
| Incandescent Heart | Body Armour | Light Radius is based on Energy Shield instead of Life | Defence | `light_radius_scales_with_energy_shield` |
| Indigon | Helmet | Recover (8-10)% of Life when you use a Mana Flask | Defence | `recover_%_maximum_life_on_mana_flask_use` |
| Inextricable Fate | Boots | You gain 3 Grasping Vines when you take a Critical Strike | Defence | `gain_x_grasping_vines_when_you_take_a_critical_strike` |
| Jiquani's Potential | Staff | (-17-17)% reduced maximum Life | Defence | `maximum_life_+%` |
| Kiloava's Bluster | Shield | (30-40)% chance for Elemental Resistances to count as being 90% against Enemy Hits | Defence | `enemy_hits_%_chance_to_treat_elemental_resistances_as_90%` |
| Kingsguard | Body Armour | Gain 100 Life when you lose an Endurance Charge | Defence | `gain_x_life_when_endurance_charge_expires_or_consumed` |
| Leadership's Price | Amulet | +(-3-3)% to maximum Cold Resistance | Defence | — |
| Leadership's Price | Amulet | +(-3-3)% to maximum Fire Resistance | Defence | — |
| Leadership's Price | Amulet | +(-3-3)% to maximum Lightning Resistance | Defence | — |
| Lightbane Raiment | Body Armour | 100% chance to create Desecrated Ground when you Block | Defence | `desecrate_on_block_%_chance_to_create` |
| Lochtonial Caress | Gloves | (10-15)% chance to gain a Power, Frenzy or Endurance Charge on Kill | Defence | `power_frenzy_or_endurance_charge_on_kill_%` |
| Maligaro's Lens | Shield | Allies within 3.5 metres Recover 1% of your Maximum Life when you Die | Defence | `unique_nearby_allies_recover_permyriad_max_life_on_death` |
| Mark of the Elder | Ring | Cannot be Stunned by Attacks if your opposite Ring is an Elder Item | Defence | `cannot_be_stunned_by_attacks_if_other_ring_is_elder_item` |
| Mark of the Shaper | Ring | Cannot be Stunned by Spells if your opposite Ring is a Shaper Item | Defence | `cannot_be_stunned_by_spells_if_other_ring_is_shaper_item` |
| Mask of the Spirit Drinker | Helmet | Your Energy Shield starts at zero | Defence | `keystone_soul_tether`, `start_at_zero_energy_shield` |
| Mask of the Stitched Demon | Helmet | Your Energy Shield starts at zero | Defence | `keystone_soul_tether`, `start_at_zero_energy_shield` |
| Matua Tupuna | Shield | Spreads Tar when you Block | Defence | `ground_tar_on_block_base_area_of_effect_radius` |
| Mercenary's Lot | Gloves | 8% of Damage from Hits is taken from Marked Target's Life before you | Defence | `damage_removed_from_marked_target_before_life_or_es_%` |
| Mind of the Council | Helmet | +20% chance to be Shocked | Defence | `chance_to_be_shocked_%` |
| Mind of the Council | Helmet | Lose 3% of Mana when you use an Attack Skill | Defence | `lose_%_of_mana_when_you_use_an_attack_skill` |
| Mindspiral | Helmet | Enemies Cannot Leech Mana From you | Defence | `cannot_have_mana_leeched_from` |
| Mokou's Embrace | Ring | +25% chance to be Ignited | Defence | `chance_to_be_ignited_%` |
| Mokou's Embrace | Ring | All Damage Taken from Hits can Ignite you | Defence | `all_damage_taken_can_ignite` |
| Mortem Morsu | Claw | 25% reduced Enemy Stun Threshold with this Weapon | Defence | `local_stun_threshold_reduction_+%` |
| Ngamahu's Sign | Ring | Recover (20-30) Life when you Ignite an Enemy | Defence | `recover_X_life_on_enemy_ignited` |
| Null and Void | Gloves | Removes Elemental Ailments on Rampage | Defence | `dispel_status_ailments_on_rampage_threshold` |
| Olroth's Charge | Boots | Gain Adrenaline for 3 seconds when Ward Breaks | Defence | `gain_adrenaline_when_ward_breaks_ms` |
| Olroth's Resolve | Flask | Restores Ward on use | Defence | `local_flask_restore_ward` |
| Orbala's Stand | Boots | Cannot be Stunned by Suppressed Spell Damage | Defence | `cannot_be_stunned_by_suppressed_spell_damage` |
| Original Sin | Ring | Chaos Resistance of Enemies within 6 metres is 0 | Defence | `local_display_nearby_enemy_no_chaos_damage_resistance` |
| Perseverance | Belt | Melee Hits which Stun Fortify | Defence | `chance_to_fortify_on_melee_stun_%` |
| Queen of the Forest | Body Armour | -(50-40) Physical Damage taken from Hits by Animals | Defence | `physical_damage_taken_+_vs_beasts` |
| Rapid Expansion | Jewel | to grant an Endurance Charge when you Stun an Enemy | Defence | — |
| Rathpith Globe | Shield | Sacrifice 10% of your Life when you Use or Trigger a Spell Skill | Defence | `sacrifice_%_life_on_spell_skill` |
| Razor of the Seventh Sun | One Handed Sword | Recover 1% of Life when you Ignite an Enemy | Defence | `recover_%_maximum_life_on_enemy_ignited` |
| Remnant of Empires | Shield | 50% chance to gain an Endurance Charge when you Block | Defence | `chance_to_gain_endurance_charge_on_block_%` |
| Replica Allure | Claw | Gain +50 Life when you Taunt an Enemy | Defence | `life_gained_on_taunting_enemy` |
| Replica Ambu's Charge | Body Armour | Gain an Endurance Charge when you are Hit | Defence | `chance_to_gain_endurance_charge_when_hit_%` |
| Replica Ambu's Charge | Body Armour | Share Endurance Charges with Party members within 12 metres | Defence | `endurance_only_conduit` |
| Replica Badge of the Brotherhood | Amulet | (20-25)% chance to lose an Endurance Charge when you gain Fortification | Defence | `lose_an_endurance_charge_on_fortify_gain_%_chance` |
| Replica Farrul's Fur | Body Armour | Gain up to your maximum number of Frenzy and Endurance Charges when you gain Cat's Agility | Defence | `gain_maximum_frenzy_and_endurance_charges_when_you_gain_cats_agility` |
| Replica Fragility | Jewel | Lose an Endurance Charge each second | Defence | `gain_X_endurance_charges_per_second` |
| Replica Oro's Sacrifice | Two Handed Sword | Gain an Endurance Charge if an Attack Freezes an Enemy | Defence | `gain_endurance_charge_if_attack_freezes` |
| Replica Reckless Defence | Jewel | +10% chance to be Frozen, Shocked and Ignited | Defence | `chance_to_be_frozen_shocked_ignited_%` |
| Replica Rumi's Concoction | Flask | Gain 1 Endurance Charge on use | Defence | `local_flask_gain_endurance_charges_on_use` |
| Replica Rumi's Concoction | Flask | Petrified during Effect | Defence | `local_flask_is_petrified` |
| Replica Ungil's Gauche | Dagger | Chill Attackers for 4 seconds on Block | Defence | `chill_attackers_for_4_seconds_on_block_%_chance` |
| Replica Unstable Payload | Jewel | Recover (20-30) Life when your Trap is triggered by an Enemy | Defence | `gain_x_life_on_trap_triggered_by_an_enemy` |
| Replica Victario's Charity | Shield | 5% chance to grant an Endurance Charge to Allies within 4 metres on Hit | Defence | `chance_to_grant_endurance_charge_to_nearby_allies_on_hit_%` |
| Ryslatha's Coil | Belt | Gain 50 Life when you Stun an Enemy | Defence | `gain_X_life_on_stun` |
| Sandstorm Visage | Helmet | Ignore Stuns while Casting | Defence | `avoid_interruption_while_casting_%` |
| Sentari's Answer | Shield | Curse Enemies with Elemental Weakness when you Block their Spell Damage, ignoring Curse Limit | Defence | `curse_on_spell_block_level_15_elemental_weakness` |
| Sentari's Answer | Shield | Curse Enemies with Punishment when you Block their Melee Damage, ignoring Curse Limit | Defence | `curse_on_melee_block_level_15_punishment` |
| Sentari's Answer | Shield | Curse Enemies with Temporal Chains when you Block their Projectile Attack Damage, ignoring Curse Limit | Defence | `curse_on_projectile_block_level_15_temporal_chains` |
| Shackles of the Wretched | Gloves | You cannot be Chilled for 3 seconds after being Chilled | Defence | `chill_prevention_ms_when_chilled` |
| Shackles of the Wretched | Gloves | You cannot be Frozen for 3 seconds after being Frozen | Defence | `freeze_prevention_ms_when_frozen` |
| Shackles of the Wretched | Gloves | You cannot be Ignited for 3 seconds after being Ignited | Defence | `ignite_prevention_ms_when_ignited` |
| Shackles of the Wretched | Gloves | You cannot be Shocked for 3 seconds after being Shocked | Defence | `shock_prevention_ms_when_shocked` |
| Sin Trek | Boots | Enemies Cannot Leech Life From you | Defence | `cannot_have_life_leeched_from` |
| Sin's Rebirth | Flask | Removes all Burning when used | Defence | — |
| Soul Mantle | Body Armour | Inflicts a random Hex on you when your Totems die | Defence | `randomly_cursed_when_totems_die_curse_level` |
| Spire of Stone | Jewel | Totems cannot be Stunned | Defence | `totems_cannot_be_stunned` |
| Starlight Chalice | Flask | Restores Ward on use | Defence | `local_flask_restore_ward` |
| Sudden Dawn | Helmet | (10-20)% chance for Energy Shield Recharge to start when you Kill an Enemy | Defence | `energy_shield_recharges_on_kill_%` |
| Sunspite | Boots | +25% chance to be Ignited | Defence | `chance_to_be_ignited_%` |
| Surgebinders | Gloves | 10% chance to Steal Power, Frenzy, and Endurance Charges on Hit | Defence | `base_steal_power_frenzy_endurance_charges_on_hit_%` |
| Tainted Pact | Amulet | Taking Chaos Damage over Time heals you instead while Leeching Life | Defence | `chaos_damage_over_time_heals_while_leeching_life` |
| Tanu Ahi | Gloves | 10% chance to gain Adrenaline for 2 Seconds when Leech is | Defence | — |
| Tanu Ahi | Gloves | 10% chance to gain Onslaught for 4 Seconds when Leech is | Defence | — |
| Tanu Ahi | Gloves | removed by Filling Unreserved Life | Defence | — |
| Tanu Ahi | Gloves | removed by Filling Unreserved Life | Defence | — |
| Tavukai | Amulet | Minions have +(-17-17)% to Chaos Resistance | Defence | — |
| Tavukai | Amulet | Summoned Raging Spirits take 20% of their Maximum Life per second as Chaos Damage | Defence | `minion_raging_spirit_%_of_maximum_life_taken_per_minute_as_chaos_damage` |
| Tawhanuku's Timing | Ring | Spells cause you to gain Energy Shield equal to their Upfront | Defence | — |
| Tawhoa's Felling | Two Handed Mace | (20-30)% reduced Enemy Stun Threshold with this Weapon | Defence | `local_stun_threshold_reduction_+%` |
| Temptation Step | Boots | have fewer than 5 Poisons on you | Defence | — |
| The Baron | Helmet | With at least 1000 Strength, (1.5-2)% of Damage dealt by your Raised Zombies is Leeched to you as Life | Defence | `zombie_damage_leeched_as_life_to_you_permyriad_if_over_1000_strength` |
| The Battle Within | Tincture | Inflicts Mana Burn on you when you Hit an Enemy with a Melee Weapon | Defence | — |
| The Blue Dream | Jewel | Passives granting Lightning Resistance or all Elemental Resistances in Radius | Defence | — |
| The Bringer of Rain | Helmet | 20% chance to gain an Endurance Charge when you Block | Defence | `chance_to_gain_endurance_charge_on_block_%` |
| The Broken Elegy | Staff | When a Minion within 4 metres dies, gain Rotten Bulwark equal to (7-9)% of its maximum Life | Defence | `minion_life_%_to_gain_as_flesh_shield_on_nearby_minion_death` |
| The Celestial Brace | Gloves | Melee Hits from Strike Skills Fortify | Defence | `strike_skills_fortify_on_hit` |
| The Devouring Diadem | Helmet | 10% chance for Energy Shield Recharge to start when you use a Skill | Defence | `energy_shield_recharges_on_skill_use_chance_%` |
| The Druggery | Belt | 100% of Life Recovery from Flasks is applied to Allies within 7.5 metres instead of You | Defence | `life_recovery_from_flasks_instead_applies_to_nearby_allies_%` |
| The Eternal Apple | Shield | Trigger a Socketed Warcry Skill on losing Endurance Charges, with a 0.25 second Cooldown | Defence | `trigger_socketed_warcry_when_endurance_charge_expires_or_consumed_%_chance` |
| The Eternal Apple | Shield | You lose all Endurance Charges on reaching maximum Endurance Charges | Defence | `lose_all_endurance_charges_when_reaching_maximum` |
| The Flawed Refuge | Shield | You take 100% of Elemental Damage from Blocked Hits | Defence | `block_%_damage_taken_from_elemental` |
| The Fledgling | Helmet | Projectiles cannot collide with Enemies in Close Range | Defence | `close_range_enemies_avoid_your_projectiles` |
| The Goddess Unleashed | One Handed Sword | 100% chance to Avoid being Ignited, Chilled or Frozen with Her Blessing | Defence | `avoid_freeze_chill_ignite_%_with_her_blessing` |
| The Green Dream | Jewel | Passives granting Cold Resistance or all Elemental Resistances in Radius | Defence | — |
| The Gull | Helmet | (25-50)% increased Duration of Shrine Effects on you | Defence | `shrine_effect_duration_+%` |
| The Highwayman | Ring | Steal Power, Frenzy, and Endurance Charges on Hit | Defence | `base_steal_power_frenzy_endurance_charges_on_hit_%` |
| The Infinite Pursuit | Boots | 50% chance to be inflicted with Bleeding when Hit by an Attack | Defence | `receive_bleeding_chance_%_when_hit_by_attack` |
| The Infinite Pursuit | Boots | Bleeding on you expires 75% slower while Moving | Defence | `bleeding_on_self_expire_speed_+%_while_moving` |
| The Monastery Bell | One Handed Mace | Count as Blocking Attack Damage from the first target Hit with each Shield Attack | Defence | `count_as_blocking_attack_from_shield_attack_first_target` |
| The Primordial Chain | Amulet | You cannot have non-Golem Minions | Defence | `you_cannot_have_non_golem_minions` |
| The Princess | One Handed Sword | 10% increased Damage taken from Ghosts | Defence | `damage_taken_+%_from_ghosts` |
| The Princess | One Handed Sword | 10% increased Damage taken from Skeletons | Defence | `damage_taken_+%_from_skeletons` |
| The Red Dream | Jewel | Passives granting Fire Resistance or all Elemental Resistances in Radius | Defence | — |
| The Red Dream | Jewel | also grant an equal chance to gain an Endurance Charge on Kill | Defence | — |
| The Red Trail | Boots | 50% chance to be inflicted with Bleeding when Hit by an Attack | Defence | `receive_bleeding_chance_%_when_hit_by_attack` |
| The Retch | Belt | 200% of Life Leech applies to Enemies as Chaos Damage | Defence | `life_leech_applies_to_enemies_%` |
| The Stormwall | Staff | (30-40)% chance to Chill Attackers for 4 seconds on Block | Defence | `chill_attackers_for_4_seconds_on_block_%_chance` |
| The Untouched Soul | Amulet | Players have +12% to all Elemental Resistances for each Empty White Socket | Defence | — |
| The Untouched Soul | Amulet | Players have +40 to maximum Life for each Empty Red Socket on any Equipped Item | Defence | `maximum_life_+_per_empty_red_socket` |
| The Vertex | Helmet | Enemies Cannot Leech Mana From you | Defence | `cannot_have_mana_leeched_from` |
| The Vigil | Jewel | With at least 40 Strength in Radius, Hits with Vigilant Strike Fortify you and Allies within a 10 metre base radius for 8 seconds | Defence | `local_unique_jewel_vigilant_strike_fortifies_nearby_allies_for_x_seconds_with_50_str_in_radius` |
| Thirst for Horrors | Shield | 10% Chance to Cause Monster to Flee on Block | Defence | `block_causes_monster_flee_%` |
| Tidebreaker | Two Handed Mace | (20-30)% reduced Enemy Stun Threshold with this Weapon | Defence | `local_stun_threshold_reduction_+%` |
| Tinkerskin | Body Armour | Recover 100 Life when your Trap is triggered by an Enemy | Defence | `gain_x_life_on_trap_triggered_by_an_enemy` |
| Tinkerskin | Body Armour | Recover 50 Energy Shield when your Trap is triggered by an Enemy | Defence | `gain_x_es_on_trap_triggered_by_an_enemy` |
| Titucius' Span | Shield | 200% increased Armour against Projectiles | Defence | `physical_damage_reduction_rating_+%_against_projectiles` |
| Ulaman's Gaze | Jewel | Projectiles have 4% chance to be able to Chain when colliding with terrain per | Defence | — |
| Uul-Netol's Vow | Amulet | +(-23-23)% to Chaos Resistance | Defence | — |
| Uul-Netol's Vow | Amulet | +(-30-30)% to Cold Resistance | Defence | — |
| Uul-Netol's Vow | Amulet | +(-30-30)% to Fire Resistance | Defence | — |
| Uul-Netol's Vow | Amulet | +(-30-30)% to Lightning Resistance | Defence | — |
| Veil of Flesh | Helmet | Maximum Bitterblood is equal to your Maximum Life | Defence | `flesh_barrier_maximum_equal_to_%_of_maximum_life` |
| Vessel of Vinktar | Flask | You are Shocked during Effect, causing 50% increased Damage taken | Defence | `local_unique_flask_shocked_during_flask_effect` |
| Violent Dead | Jewel | Zombies' Slam Attack has 100% increased Cooldown Recovery Rate | Defence | — |
| Vivinsect | Ring | (3-4)% chance to gain an Endurance Charge on Kill | Defence | `endurance_charge_on_kill_%` |
| Voidbringer | Gloves | Lose (40-80) Mana when you use a Skill | Defence | `lose_x_mana_when_you_use_skill` |
| Voll's Devotion | Amulet | Gain an Endurance Charge when you lose a Power Charge | Defence | `gain_endurance_charge_on_power_charge_expiry` |
| Vorana's Preparation | Flask | Effect is removed when Ward Breaks | Defence | `local_flask_remove_effect_when_ward_breaks` |
| Vorana's Preparation | Flask | Restores Ward on use | Defence | `local_flask_restore_ward` |
| Wellwater Phylactery | Flask | Energy Shield Recharge is not delayed by Damage during Effect | Defence | `local_flask_energy_shield_recharge_not_delayed_by_damage_during_effect` |
| Wellwater Phylactery | Flask | Removes (10-15)% of Life when Used | Defence | `local_unique_flask_instantly_removes_%_maximum_life` |
| Wellwater Phylactery | Flask | Starts Energy Shield Recharge when Used | Defence | `local_unique_flask_start_energy_shield_recharge` |
| Whakatutuki o Matua | Shield | Spreads Tar when you Block | Defence | `ground_tar_on_block_base_area_of_effect_radius` |
| Wheel of the Stormsail | Shield | 100% increased Duration of Curses on you | Defence | `self_curse_duration_+%` |
| Willclash | Helmet | Lose all Power Charges when you Block | Defence | `lose_all_power_charges_on_block` |
| Wraithlord | Helmet | You cannot have Non-Spectre Minions | Defence | `you_cannot_have_non_spectre_minions` |
| Wyrmsign | Gloves | Lose all Endurance Charges when Rampage ends | Defence | `lose_endurance_charges_on_rampage_end` |
| Xirgil's Crank | Staff | (25-35)% chance for Energy Shield Recharge to start when you Block | Defence | `energy_shield_recharges_on_block_%` |
| Xoph's Nurture | Bow | Recover (40-60) Life when you Ignite an Enemy | Defence | `recover_X_life_on_enemy_ignited` |
| Yaomac's Accord | Sceptre | Gain an Endurance Charge, Frenzy Charge, and Power Charge when you use a Vaal Skill | Defence | `gain_frenzy_power_endurance_charges_on_vaal_skill_use` |
| Zahndethus' Cassock | Body Armour | 100% chance to create Consecrated Ground when you Block | Defence | `consecrate_on_block_%_chance_to_create` |
| Zana's Ingenuity | Ring | +(-15-15)% to all Elemental Resistances | Defence | — |
| Adamant | Notable | Remove Bleeding when you use a Guard Skill | Defence | `dispel_bleed_on_guard_skill_use` |
| Adamant | Notable | Remove Corrupted Blood when you use a Guard Skill | Defence | `dispel_corrupted_blood_on_guard_skill_use` |
| Aggressive Bastion | Notable | 10% chance to gain an Endurance Charge on Kill while holding a Shield | Defence | `endurance_charge_on_kill_percent_chance_while_holding_shield` |
| Aggressive Defence | Notable | Fortifying Hits grant 60% increased Fortification | Defence | `fortification_gained_from_hits_+%` |
| Ancestral Guidance | Notable | Totems Regenerate 2% of Life per second | Defence | `totems_regenerate_%_life_per_minute` |
| Bannerman | Notable | Your Banner Buffs Linger on you for 3 seconds after you leave the Area | Defence | `banner_buff_lingers_for_X_seconds_after_leaving_area` |
| Bloodless | Notable | Enemies Cannot Leech Life From you | Defence | `cannot_have_life_leeched_from` |
| Bomb Specialist | Saboteur | 30% chance to take 50% less Area Damage from Hits | Defence | `take_half_area_damage_from_hit_%_chance` |
| Bone Barrier | Necromancer | 1% of Damage Dealt by your Minions is Leeched to you as Life | Defence | `life_leech_from_minion_damage_%` |
| Boon of the River | Olroth | 5% chance to Restore your Ward on Hit | Defence | `restore_ward_on_hit_%` |
| Bound Flesh | Necromantic | Maximum Baryatic Tension is equal to 30% of maximum Life | Defence | `maximum_blood_phylactery_%_of_life` |
| Bound Flesh | Necromantic | When you take a Savage Hit, lose Baryatic Tension to recover that much Life, up to maximum | Defence | `recover_from_blood_phylactery_on_savage_hit_taken` |
| Brutal Blade | Notable | 20% chance to gain a Frenzy Charge when you Block Attack Damage | Defence | `chance_to_gain_frenzy_charge_on_block_attack_%` |
| Burst of Energy | Notable | Recover 15% of Mana when you activate a Tincture | Defence | `recover_%_maximum_mana_on_activating_tincture` |
| Capacitor | Notable | You cannot be Shocked if you've been Shocked Recently | Defence | `cannot_be_shocked_if_you_have_been_shocked_recently` |
| Cauterisation | Notable | Bleeding enemies cannot inflict Bleeding on you | Defence | `cannot_be_bled_by_bleeding_enemies` |
| Champion | Ascendant | Melee Hits have 50% chance to Fortify | Defence | `chance_to_fortify_on_melee_hit_+%` |
| Charge on Kill | Normal | 2% chance to gain a Power, Frenzy or Endurance Charge on Kill | Defence | `power_frenzy_or_endurance_charge_on_kill_%` |
| Charge on Kill | Normal | 2% chance to gain a Power, Frenzy or Endurance Charge on Kill | Defence | `power_frenzy_or_endurance_charge_on_kill_%` |
| Claws of the Magpie | Notable | 25% chance to Steal Power, Frenzy, and Endurance Charges on Hit with Claws | Defence | `claw_steal_power_frenzy_endurance_charges_on_hit_%` |
| Crushing Reply | Notable | Retaliation Skills Fortify on Melee Hit | Defence | `retaliation_skills_fortify_on_melee_hit` |
| Defiant Stand | Notable | Gain 3 Endurance Charges when you consume maximum Valour to place a Banner | Defence | `banner_gain_X_endurance_charges_when_placed_with_max_resources` |
| Defiled Forces | Notable | Remove Elemental Ailments when you Cast a Curse Spell | Defence | `remove_elemental_ailments_on_curse_cast_%` |
| Deflection | Notable | 25% chance to gain an Endurance Charge when you Block | Defence | `chance_to_gain_endurance_charge_on_block_%` |
| Disciple of Kitava | Keystone | Every second, Consume a nearby Corpse to Recover 5% of Life and Mana | Defence | — |
| Disciple of the Unyielding | Notable | 8% chance to gain an Endurance Charge on Kill | Defence | `endurance_charge_on_kill_%` |
| Disease Vector | Notable | Enemies Poisoned by you cannot Regenerate Life | Defence | `enemies_poisoned_by_you_cannot_regen_life` |
| Efficient Explosives | Notable | Mines have a 15% chance to be Detonated an Additional Time | Defence | `mine_%_chance_to_detonate_twice` |
| Eldritch Battery | Keystone | Spend Energy Shield before Mana for Skill Mana Costs | Defence | — |
| Endless Hunger | Slayer | 20% of Overkill Damage is Leeched as Life | Defence | `life_leech_on_overkill_damage_%` |
| Enduring Composure | Notable | Gain 1 Endurance Charge every second if you've been Hit Recently | Defence | `gain_endurance_charge_per_second_if_have_been_hit_recently` |
| Enduring Focus | Notable | 25% chance to gain an Endurance Charge each second while Channelling | Defence | `%_chance_to_gain_endurance_charge_each_second_while_channelling` |
| Enduring Suffusion | Raider | Tincture Effects Linger on you for 0.5 seconds per Mana Burn on you when the Tincture was deactivated, up to a maximum of 6 seconds | Defence | `tincture_effects_linger_for_ms_per_toxicity_up_to_6_seconds` |
| Enduring Ward | Notable | 20% chance to gain an Endurance Charge when you Block | Defence | `chance_to_gain_endurance_charge_on_block_%` |
| Enigmatic Reach | Notable | 25% chance to gain a Power Charge when you Block Spell Damage | Defence | `power_charge_on_spell_block_%_chance` |
| Entrench | Notable | Life Flasks gain 3 Charges when you Suppress Spell Damage | Defence | `life_flasks_gain_X_charges_on_suppressing_spell` |
| Expert Sabotage | Notable | Mines have a 10% chance to be Detonated an Additional Time | Defence | `mine_%_chance_to_detonate_twice` |
| Fiery Aegis | Notable | Hallowing Flame you inflict has 1% increased magnitude per 2% Attack Block chance | Defence | `hallowing_flame_magnitude_+%_per_2%_attack_block_chance` |
| Fire Attunement | Notable | You cannot be Ignited if you've been Ignited Recently | Defence | `cannot_be_ignited_if_you_have_been_ignited_recently` |
| First to Strike, Last to Fall | Champion | Recover 25% of Life when you gain Adrenaline | Defence | `recover_%_life_when_gaining_adrenaline` |
| First to Strike, Last to Fall | Champion | Remove all Ailments and Burning when you gain Adrenaline | Defence | `remove_ailments_and_burning_on_gaining_adrenaline` |
| Focal Point | Deadeye | 25% less Damage taken from other Enemies near your Marked Enemy | Defence | `damage_taken_+%_final_from_enemies_near_marked_enemy` |
| Fortification Gain | Normal | Fortifying Hits grant 40% increased Fortification | Defence | `fortification_gained_from_hits_+%` |
| Fortification Gain | Normal | Fortifying Hits grant 40% increased Fortification | Defence | `fortification_gained_from_hits_+%` |
| Fortify on Melee Stun | Normal | Melee Hits which Stun have 10% chance to Fortify | Defence | `chance_to_fortify_on_melee_stun_%` |
| Fortify on Melee Stun | Normal | Melee Hits which Stun have 10% chance to Fortify | Defence | `chance_to_fortify_on_melee_stun_%` |
| Ghost Dance | Keystone | When Hit, lose a Ghost Shroud to Recover Energy Shield equal to 3% of your Evasion Rating | Defence | — |
| Hex Breaker | Notable | Remove a Curse after Channelling for 2 seconds | Defence | `remove_x_curses_after_channelling_for_2_seconds` |
| Hibernator | Notable | You cannot be Frozen if you've been Frozen Recently | Defence | `cannot_be_frozen_if_you_have_been_frozen_recently` |
| Inexorable | Notable | 25% chance to gain an Endurance Charge when you are Hit | Defence | `chance_to_gain_endurance_charge_when_hit_%` |
| Inspirational | Champion | When you leave your Banner's Area, recover 30% of the Valour consumed for that Banner | Defence | `on_leaving_banner_area_recover_%_of_planted_banner_resources` |
| Inspiring Bond | Notable | 10% chance for Energy Shield Recharge to start when you Link to a target | Defence | `chance_to_start_energy_shield_recharge_%_on_linking_target` |
| Invigorating Blaze | Notable | Recover 2% of Life when you Ignite a non-Ignited Enemy | Defence | `recover_%_life_when_you_ignite_a_non_ignited_enemy` |
| Juggernaut | Ascendant | Gain 1 Endurance Charge every second if you've been Hit Recently | Defence | `gain_endurance_charge_per_second_if_have_been_hit_recently` |
| Last Rites | Notable | Enemies you Curse cannot Recharge Energy Shield | Defence | `enemies_you_curse_cannot_recharge_energy_shield` |
| Life from Death | Notable | Minions Recover 4% of Life on Minion Death | Defence | `minion_recover_%_maximum_life_on_minion_death` |
| Loyal Bodyguard | Luminary | If your Mercenary's Life is lower than your own, 40% of Damage they take is Recouped as Life | Defence | `permanenet_mercenary_damage_taken_recouped_as_life_%_if_life_lower_than_parents_life` |
| Mage Bane | Notable | 20% chance to gain a Power Charge when you Block | Defence | `chance_to_gain_power_charge_when_block_%` |
| Mage Hunter | Notable | 20% chance to gain a Power Charge when you Block | Defence | `chance_to_gain_power_charge_when_block_%` |
| Master Alchemist | Pathfinder | Removes Ailments when you use a Flask | Defence | `dispel_status_ailments_on_flask_use` |
| Mender's Wellspring | Notable | Remove Bleeding when you use a Life Flask | Defence | `remove_bleed_on_life_flask_use` |
| Mercenary Life, Light Radius | Luminary | Your Mercenary and their Minions have 15% increased maximum Life | Defence | `permanenet_mercenary_maximum_life_+%_and_minion_maximum_life_+%` |
| Mercenary Life, Light Radius | Luminary | Your Mercenary and their Minions have 15% increased maximum Life | Defence | `permanenet_mercenary_maximum_life_+%_and_minion_maximum_life_+%` |
| Natural Remedies | Notable | Remove Maim and Hinder when you use a Flask | Defence | `remove_maim_and_hinder_on_flask_use` |
| Overcharged | Notable | 8% chance to gain a Power, Frenzy or Endurance Charge on Kill | Defence | `power_frenzy_or_endurance_charge_on_kill_%` |
| Overlord | Notable | Melee Hits with Maces, Sceptres or Staves Fortify for 6 seconds | Defence | `gain_fortify_for_x_seconds_on_melee_hit_with_mace_sceptre_staff` |
| Pathfinder | Ascendant | Removes Bleeding when you use a Flask | Defence | `remove_bleed_on_flask_use` |
| Powerful Ward | Notable | 20% chance to gain a Power Charge when you Block | Defence | `chance_to_gain_power_charge_when_block_%` |
| Purposeful Harbinger | Notable | Auras from your Skills have 8% increased Effect on you for | Defence | — |
| Rampart | Notable | Fortifying Hits against Unique Enemies grant 100% increased Fortification | Defence | `fortification_gained_from_hits_+%_against_unique_enemies` |
| Ricochet | Deadeye | Projectiles have 30% chance to be able to Chain when colliding with terrain | Defence | `projectile_chain_from_terrain_chance_%` |
| Rote Reinforcement | Notable | 20% chance to gain an Endurance Charge when you Block | Defence | `chance_to_gain_endurance_charge_on_block_%` |
| Smashing Strikes | Notable | 10% chance to gain an Endurance Charge on Melee Critical Strike | Defence | `chance_to_gain_endurance_charge_on_melee_crit_%` |
| Spellbreaker | Trickster | 50% chance for Energy Shield Recharge to start when you Suppress Spell Damage | Defence | `energy_shield_recharges_on_suppress_%` |
| Swagger | Notable | 25% chance to gain a Frenzy Charge when you Block | Defence | `chance_to_gain_frenzy_charge_on_block_%` |
| That didn't happen! | Delirious | Four seconds after each Hit you take, lose Life equal to 40% of the Damage taken from that Hit | Defence | `four_seconds_after_being_hit_lose_life_equal_to_x%_of_hit` |
| That didn't happen! | Delirious | Take 40% less Damage from Hits | Defence | `alternate_ascendancy_damage_taken_when_hit_+%_final` |
| The Monastery Bell | Reliquarian | Count as Blocking Attack Damage from the first target Hit with each Shield Attack | Defence | `count_as_blocking_attack_from_shield_attack_first_target` |
| The Vivid Cat | Oshabi | Elusive has 50% chance to be removed from you at 100% effect | Defence | `elusive_has_50%_chance_to_be_removed_and_reapplied_at_%_elusive_effect` |
| Tidebreaker | Reliquarian | Gain an Endurance Charge when you Stun an Enemy with a Melee Hit | Defence | `gain_endurance_charge_on_melee_stun`, `gain_endurance_charge_on_melee_stun_%` |
| Time of Need | Guardian | Every 4 seconds, remove Curses and Ailments from you | Defence | `guardian_remove_curses_and_status_ailments_every_10_seconds` |
| Toxic Delivery | Assassin | Recover 0.5% of Life per Poison affecting Enemies you Kill | Defence | `recover_permyriad_maximum_life_per_poison_on_enemy_on_kill` |
| Trial of the Faith | Notable | Regenerate 5% of Energy Shield over 1 second when Stunned | Defence | `regenerate_%_energy_shield_over_1_second_when_stunned` |
| Trial of the Faith | Notable | Regenerate 5% of Life over 1 second when Stunned | Defence | `regenerate_%_life_over_1_second_when_stunned` |
| Unfaltering | Notable | 10% of Damage taken from Stunning Hits is Recovered as Life | Defence | `damage_taken_%_recovered_as_life_from_stunning_hits` |
| Unflinching | Juggernaut | 25% chance that if you would gain Endurance Charges, you instead gain up to maximum Endurance Charges | Defence | `gain_maximum_endurance_charges_on_endurance_charge_gained_%_chance` |
| Unflinching | Juggernaut | 30% chance to gain an Endurance Charge when you are Hit | Defence | `chance_to_gain_endurance_charge_when_hit_%` |
| Unflinching | Juggernaut | Gain 1 Endurance Charge every second if you've been Hit Recently | Defence | `gain_endurance_charge_per_second_if_have_been_hit_recently` |
| Unleashed Potential | Ascendant | 25% chance to gain a Power, Frenzy or Endurance Charge on Kill | Defence | `power_frenzy_or_endurance_charge_on_kill_%` |
| Unyielding | Juggernaut | 25% chance to gain an Endurance Charge when you Stun an Enemy | Defence | `chance_to_gain_endurance_charge_when_you_stun_enemy_%` |
| Whirling Barrier | Notable | 20% chance to gain a Power Charge when you Block | Defence | `chance_to_gain_power_charge_when_block_%` |
| Wicked Ward | Keystone | Energy Shield Recharge is not interrupted by Damage if Recharge began Recently | Defence | — |

## Unsupported · Utility (409)

| Source | Where | Line | Impact | Game stat id |
|---|---|---|---|---|
| Advancing Fortress | Claw | Reflects (71-90) Physical Damage to Melee Attackers | Utility | `physical_damage_to_return_to_melee_attacker` |
| Allelopathy | Gloves | Blight has (20-30)% increased Hinder Duration | Utility | `blight_secondary_skill_effect_duration_+%` |
| Allure | Claw | You gain Phasing for 10 seconds on using a Vaal Skill | Utility | `phase_on_vaal_skill_use_duration_ms` |
| Astral Projector | Ring | Nova Spells Cast at the targeted location instead of around you | Utility | `nova_spells_cast_at_target_location`, `nova_spells_cast_at_target_location_description_mode` |
| Atziri's Mirror | Shield | Hex Reflection | Utility | `reflect_curses` |
| Atziri's Reflection | Shield | Hex Reflection | Utility | `reflect_curses` |
| Aukuna's Will | Gloves | Raise Zombie does not require a corpse | Utility | `raise_zombie_does_not_use_corpses` |
| Aukuna's Will | Gloves | Your Raised Zombies count as corpses | Utility | `raised_zombies_are_usable_as_corpses_when_alive` |
| Balefire | Sceptre | 10% increased Scorching Ray beam length | Utility | `fire_beam_length_+%` |
| Baleful Dominion | Jewel | Historic | Utility | `local_is_alternate_tree_jewel` |
| Baleful Dominion | Jewel | Passives affected are Conquered by the Abyssal | Utility | — |
| Bisco's Collar | Amulet | +(100-150)% to Rarity of Items Dropped by Slain Magic Enemies | Utility | `magic_monster_dropped_item_rarity_+%` |
| Bitter Instinct | Shield | Reflects (200-300) Physical Damage to Melee Attackers | Utility | `physical_damage_to_return_to_melee_attacker` |
| Bitterbind Point | Shield | Your Raised Spectres also gain Arcane Surge when you do | Utility | `spectres_gain_arcane_surge_when_you_do` |
| Blackheart | Ring | 10% chance to Cause Monsters to Flee | Utility | `local_hit_causes_monster_flee_%` |
| Bloodsoaked Medallion | Amulet | Every 10 seconds: | Utility | — |
| Bottled Faith | Flask | Consecrated Ground created by this Flask has Tripled Radius | Utility | `local_flask_area_of_consecrated_ground_+%` |
| Bottled Faith | Flask | Creates Consecrated Ground on Use | Utility | `local_consecrate_ground_on_flask_use_radius` |
| Bound Fate | Belt | Every 5 seconds, gain one of the following for 5 seconds: | Utility | — |
| Bramblejack | Body Armour | 1000% of Melee Physical Damage taken reflected to Attacker | Utility | `melee_physical_damage_taken_%_to_deal_to_attacker` |
| Breathstealer | Gloves | This item can be anointed by Cassia | Utility | — |
| Brutal Restraint | Jewel | Historic | Utility | `local_is_alternate_tree_jewel` |
| Brutal Restraint | Jewel | Passives in radius are Conquered by the Maraketh | Utility | — |
| Brute Force Solution | Jewel | Corrupted | Utility | — |
| Cane of Kulemak | Staff | (60-90)% increased Unveiled Modifier magnitudes | Utility | `unveiled_mod_effect_+%` |
| Careful Planning | Jewel | Corrupted | Utility | — |
| Chain of Endurance | Belt | Reflects (100-150) Physical Damage to Melee Attackers | Utility | `physical_damage_to_return_to_melee_attacker` |
| Chill of Corruption | Jewel | 50% chance to gain an additional Vaal Soul per Enemy Shattered | Utility | `chance_to_gain_vaal_soul_on_enemy_shatter_%` |
| Chitus' Apex | Helmet | 5% increased Experience gain | Utility | `map_experience_gain_+%` |
| Cloak of Flame | Body Armour | Reflects 100 Fire Damage to Melee Attackers | Utility | `fire_damage_to_return_to_melee_attacker` |
| Cloak of Tawm'r Isley | Body Armour | Found Magic Items drop Identified | Utility | `magic_items_drop_identified` |
| Cowl of the Ceraunophile | Helmet | Can have a second Enchantment Modifier | Utility | `local_item_can_have_x_additional_enchantments` |
| Cowl of the Ceraunophile | Helmet | This item can be anointed by Cassia | Utility | — |
| Cowl of the Cryophile | Helmet | Can have a second Enchantment Modifier | Utility | `local_item_can_have_x_additional_enchantments` |
| Cowl of the Cryophile | Helmet | This item can be anointed by Cassia | Utility | — |
| Cowl of the Thermophile | Helmet | Can have a second Enchantment Modifier | Utility | `local_item_can_have_x_additional_enchantments` |
| Cowl of the Thermophile | Helmet | This item can be anointed by Cassia | Utility | — |
| Craiceann's Chitin | Helmet | Cannot lose Crab Barriers if you have lost Crab Barriers Recently | Utility | `cannot_lose_crab_charges_if_you_have_lost_crab_charges_recently` |
| Craiceann's Pincers | Gloves | 10% chance that if you would gain a Crab Barrier, you instead gain up to | Utility | — |
| Craiceann's Pincers | Gloves | your maximum number of Crab Barriers | Utility | — |
| Crown of Thorns | Helmet | Reflects 5 Physical Damage to Melee Attackers | Utility | `physical_damage_to_return_to_melee_attacker` |
| Crown of the Pale King | Helmet | 100% of Damage you Reflect to Enemies when Hit is leeched as Life | Utility | `damage_reflected_to_enemies_%_gained_as_life` |
| Crown of the Pale King | Helmet | Reflects 100 to 150 Physical Damage to Melee Attackers | Utility | `minimum_physical_damage_to_return_to_melee_attacker`, `maximum_physical_damage_to_return_to_melee_attacker` |
| Debeon's Dirge | Two Handed Axe | Warcries Knock Back and Interrupt Enemies in a smaller Area | Utility | `warcries_knock_back_enemies` |
| Destructive Aspiration | Jewel | Historic | Utility | `local_is_alternate_tree_jewel` |
| Destructive Aspiration | Jewel | Passives affected are Conquered by the Abyssal | Utility | — |
| Disintegrator | Staff | 25% chance to gain a Siphoning Charge when you use a Skill | Utility | `gain_siphoning_charge_on_skill_use_%_chance` |
| Divine Inferno | Jewel | With at least 40 Strength in Radius, Combust is Disabled | Utility | `local_jewel_disable_combust_with_40_strength_in_radius` |
| Doryani's Delusion | Boots | Corrupted | Utility | — |
| Doryani's Delusion | Boots | Corrupted | Utility | — |
| Doryani's Delusion | Boots | Corrupted | Utility | — |
| Dread Captain's Cutlass | One Handed Sword | Can be Allflame Crafted as if Rare | Utility | — |
| Dread Captain's Cutlass | One Handed Sword | Cannot gain Intangibility | Utility | — |
| Dreadmaidens' Sacrament | Flask | (4-6)% chance for a damaging Retaliation skill to | Utility | — |
| Dreadmaidens' Sacrament | Flask | Gain (4-6) Charges when you are Hit by an Enemy | Utility | `local_flask_gain_X_charges_when_hit` |
| Dreadmaidens' Sacrament | Flask | Taunts Enemies within 3 metres on use | Utility | `local_flask_taunt_enemies_on_use_radius` |
| Dreadmaidens' Sacrament | Flask | become usable for every 100 life removed this way | Utility | — |
| Efficient Training | Jewel | Corrupted | Utility | — |
| El'Abin's Visage | Helmet | Crucible Passive Skill Tree is removed if this Modifier is removed | Utility | — |
| El'Abin's Visage | Helmet | Has a Crucible Passive Skill Tree | Utility | — |
| Elegant Hubris | Jewel | Historic | Utility | `local_is_alternate_tree_jewel` |
| Elegant Hubris | Jewel | Passives in radius are Conquered by the Eternal Empire | Utility | — |
| Emperor's Cunning | Jewel | 3% increased Character Size | Utility | `base_actor_scale_+%` |
| Emperor's Mastery | Jewel | 3% increased Character Size | Utility | `base_actor_scale_+%` |
| Emperor's Might | Jewel | 3% increased Character Size | Utility | `base_actor_scale_+%` |
| Emperor's Wit | Jewel | 3% increased Character Size | Utility | `base_actor_scale_+%` |
| Energised Armour | Jewel | Corrupted | Utility | — |
| Energy From Within | Jewel | Corrupted | Utility | — |
| Entropic Devastation | Gloves | Grants Call of Steel | Utility | — |
| Esh's Visage | Shield | Reflect Shocks applied to you to all Enemies within 3 metres | Utility | `reflect_shocks_to_enemies_in_radius` |
| Extinguishing Grasp | Jewel | Historic | Utility | `local_is_alternate_tree_jewel` |
| Extinguishing Grasp | Jewel | Passives affected are Conquered by the Abyssal | Utility | — |
| Extractor Mentis | Amulet | 5% chance to grant Chaotic Might to Enemies within 2 metres on Kill | Utility | `chance_to_grant_nearby_enemies_old_unholy_might_on_kill_%` |
| Extractor Mentis | Amulet | 5% chance to grant Onslaught to Enemies within 2 metres on Kill | Utility | `chance_to_grant_nearby_enemies_onslaught_on_kill_%` |
| Eyes of the Greatwolf | Amulet | (50-100)% increased Enchantment Modifier magnitudes | Utility | `local_enchant_stat_magnitude_+%` |
| Fairgraves' Tricorne | Helmet | You can be Touched by Tormented Spirits | Utility | `player_can_be_touched_by_tormented_spirits` |
| Fenumus' Toxins | Helmet | Aspect of the Spider inflicts Spider's Webs and Hinder every 0.5 Seconds instead | Utility | `spider_aspect_web_interval_ms_override` |
| Fertile Mind | Jewel | Corrupted | Utility | — |
| Festering Vengeance | Jewel | Historic | Utility | `local_is_alternate_tree_jewel` |
| Festering Vengeance | Jewel | Passives affected are Conquered by the Abyssal | Utility | — |
| Flesh and Spirit | Gloves | Kills grant an additional Vaal Soul if you have Rampaged Recently | Utility | `gain_an_additional_vaal_soul_on_kill_if_have_rampaged_recently` |
| Fluid Motion | Jewel | Corrupted | Utility | — |
| Fortress Covenant | Jewel | Corrupted | Utility | — |
| Fragile Bloom | Jewel | Gain 1 Fragile Regrowth each second | Utility | `local_display_gain_fragile_growth_each_second` |
| Fragile Bloom | Jewel | Lose all Fragile Regrowth when Hit | Utility | `lose_all_fragile_regrowth_when_hit` |
| Fragile Bloom | Jewel | Maximum 10 Fragile Regrowth | Utility | `base_maximum_fragile_regrowth` |
| From Dust | Jewel | Summon 4 additional Skeletons with Summon Skeletons | Utility | `summon_skeletons_num_additional_warrior_skeletons` |
| Garb of the Ephemeral | Body Armour | +10 to maximum Divine Charges | Utility | `maximum_divine_charges` |
| Garb of the Ephemeral | Body Armour | Allies within 5 metres cannot have their Action Speed modified to below Base Value | Utility | `local_display_nearby_allies_action_speed_cannot_be_reduced_below_base` |
| Garb of the Ephemeral | Body Armour | Lose all Divine Charges when you gain Divinity | Utility | — |
| Glimpse of Chaos | Helmet | Can have up to 5 Implicit Modifiers while Item has this Modifier | Utility | `local_item_implicit_modifier_limit` |
| Glorious Vanity | Jewel | Historic | Utility | `local_is_alternate_tree_jewel` |
| Glorious Vanity | Jewel | Passives in radius are Conquered by the Vaal | Utility | — |
| Goblinedge | Dagger | Gain (10-20) Mana on Culling Strike | Utility | `mana_gained_on_cull` |
| Goblinedge | Dagger | Gain (120-150) Life on Culling Strike | Utility | `life_gained_on_cull` |
| Goldrim | Helmet | Reflects 4 Physical Damage to Melee Attackers | Utility | `physical_damage_to_return_to_melee_attacker` |
| Gorgon's Gaze | Helmet | Grants Level 1 Petrification Statue | Utility | — |
| Gravebind | Gloves | Enemies within 4 metres Killed by anyone count as being Killed by you instead | Utility | `local_display_enemies_killed_nearby_count_as_being_killed_by_you` |
| Great Old One's Tentacles | Gloves | 50% chance for Impales on Enemies you Kill to Reflect Damage to Enemies within 2.2 metres | Utility | `killed_enemies_apply_impale_damage_to_nearby_enemies_on_death_%_chance` |
| Gruthkul's Pelt | Body Armour | 15% increased Character Size | Utility | `base_actor_scale_+%` |
| Hale Negator | Helmet | Gain a Spirit Charge every second | Utility | `gain_spirit_charge_every_x_ms` |
| Hale Negator | Helmet | You lose all Spirit Charges when taking a Savage Hit | Utility | `lose_spirit_charges_on_savage_hit_taken` |
| Hands of the High Templar | Gloves | Can have up to 5 Implicit Modifiers while Item has this Modifier | Utility | `local_item_implicit_modifier_limit` |
| Headhunter | Belt | When you Kill a Rare monster, you gain its Modifiers for 60 seconds | Utility | `gain_rare_monster_mods_on_kill_ms` |
| Healthy Mind | Jewel | Corrupted | Utility | — |
| Heroic Tragedy | Jewel | Historic | Utility | `local_is_alternate_tree_jewel` |
| Heroic Tragedy | Jewel | Passives in radius are Conquered by the Kalguur | Utility | — |
| Hidden Potential | Jewel | Corrupted | Utility | — |
| Hiltless | Two Handed Sword | Enemies you Attack Reflect 100 Physical Damage to you | Utility | `minimum_physical_damage_to_reflect_to_self_on_attack`, `maximum_physical_damage_to_reflect_to_self_on_attack` |
| Hrimburn | Gloves | Reflects 10 Cold Damage to Melee Attackers | Utility | `cold_damage_to_return_to_melee_attacker` |
| Hrimsorrow | Gloves | Reflects 100 Cold Damage to Melee Attackers | Utility | `cold_damage_to_return_to_melee_attacker` |
| Inertia | Jewel | Corrupted | Utility | — |
| Inextricable Fate | Boots | Stationary Enemies within 6 metres gain a Grasping Vine every 0.5 seconds | Utility | `local_display_nearby_stationary_enemies_gain_a_grasping_vine_every_x_ms` |
| Inspired Learning | Jewel | With 4 Notables Allocated in Radius, When you Kill a Rare monster, you gain 1 of its Modifiers for 20 seconds | Utility | `local_unique_jewel_with_4_notables_gain_X_random_rare_monster_mods_on_kill` |
| Intuitive Leap | Jewel | Passage | Utility | — |
| Ixchel's Temptation | Ring | Maximum Quality is 200% | Utility | `local_maximum_quality_is_%` |
| Jorrhast's Blacksteel | Two Handed Mace | Weapons you Animate create an additional copy | Utility | `animate_weapon_number_of_additional_copies` |
| Kalandra's Touch | Ring | Reflects opposite Ring | Utility | `local_ring_duplicate_other_ring` |
| Kaltenhalt | Shield | Reflects (25-50) Cold Damage to Melee Attackers | Utility | `cold_damage_to_return_to_melee_attacker` |
| Kaltensoul | Shield | Reflects (25-50) Cold Damage to Melee Attackers | Utility | `cold_damage_to_return_to_melee_attacker` |
| Kaom's Spirit | Gloves | Does not delay Inherent Loss of Rage | Utility | — |
| Khatal's Geyser | Amulet | Can't use Life Flasks | Utility | `cannot_use_life_flasks` |
| Khatal's Geyser | Amulet | Mana Flask Effects do not Queue | Utility | — |
| Khatal's Weeping | Amulet | Can't use Mana Flasks | Utility | `cannot_use_mana_flasks` |
| Kingmaker | Two Handed Axe | Insufficient Mana doesn't prevent your Melee Attacks | Utility | `melee_attacks_usable_without_mana_cost` |
| Leash of Oblation | Belt | You can have an Offering of each type | Utility | `allow_multiple_offerings` |
| Legacy of Fury | Boots | (30-40)% chance when you Kill a Scorched Enemy to Burn Each surrounding | Utility | — |
| Legacy of the Rose | Staff | Gain 1 Remembrance when you spend a total of 200 Energy | Utility | — |
| Legacy of the Rose | Staff | Maximum 10 Remembrance | Utility | `maximum_celestial_charges` |
| Legacy of the Rose | Staff | Shield with no Shaper Memory Summoned | Utility | — |
| Leper's Alms | Shield | Shared Suffering | Utility | `keystone_shared_suffering` |
| Lethal Pride | Jewel | Historic | Utility | `local_is_alternate_tree_jewel` |
| Lethal Pride | Jewel | Passives in radius are Conquered by the Karui | Utility | — |
| Lightbane Raiment | Body Armour | Reflects 30 Chaos Damage to Melee Attackers | Utility | `chaos_damage_to_return_to_melee_attacker` |
| Lightpoacher | Helmet | Gain a Spirit Charge on Kill | Utility | `gain_spirit_charge_on_kill_%_chance` |
| Lion's Roar | Flask | 75% chance to cause Enemies to Flee on use | Utility | `local_flask_use_causes_monster_flee_chance_%` |
| Lion's Roar | Flask | Knocks Back Enemies in an Area when you use a Flask | Utility | `local_flask_use_causes_area_knockback` |
| Lord of Steel | Jewel | Call of Steel deals Reflected Damage with (40-50)% increased Area of Effect | Utility | `steel_steal_area_of_effect_+%` |
| Lord of Steel | Jewel | Call of Steel has (80-100)% increased Use Speed | Utility | `steel_steal_cast_speed_+%` |
| Mageblood | Belt | Magic Utility Flask Effects cannot be removed | Utility | `magic_utility_flasks_cannot_be_removed` |
| Mageblood | Belt | Magic Utility Flasks cannot be Used | Utility | `magic_utility_flasks_cannot_be_used` |
| Malachai's Artifice | Ring | All Sockets are White | Utility | `local_all_sockets_are_white` |
| Malachai's Mark | Gloves | Grants Malachai's Endurance, Frenzy and Power for 6 seconds each, in sequence | Utility | `thaumaturgy_rotation_active` |
| Maligaro's Restraint | Belt | Shocks you cause are reflected back to you | Utility | `shocks_reflected_to_self` |
| Maloney's Nightfall | Quiver | 25% chance to create a Smoke Cloud when Hit | Utility | `ground_smoke_when_hit_%` |
| Mark of the Red Covenant | Helmet | Summoned Raging Spirits' Melee Strikes deal Fire-only Splash | Utility | — |
| Martyr's Crown | Helmet | Reflects 5 Physical Damage to Melee Attackers | Utility | `physical_damage_to_return_to_melee_attacker` |
| Mercenary's Lot | Gloves | Your Mark Transfers to another Enemy within 3 metres when Marked Enemy dies | Utility | `your_marks_transfer_to_nearby_enemies_on_death_%_chance` |
| Midnight Bargain | Wand | Cannot be used with Chaos Inoculation | Utility | `local_cannot_be_used_with_chaos_innoculation` |
| Militant Faith | Jewel | Historic | Utility | `local_is_alternate_tree_jewel` |
| Militant Faith | Jewel | Passives in radius are Conquered by the Templars | Utility | — |
| Mon'tregul's Grasp | Sceptre | 25% increased Raised Zombie Size | Utility | `zombie_scale_+%` |
| Moonsorrow | Wand | Cannot roll Caster Modifiers | Utility | `item_generation_cannot_roll_caster_affixes` |
| Nebulis | Sceptre | (60-120)% increased Implicit Modifier magnitudes | Utility | `local_implicit_stat_magnitude_+%` |
| Nuro's Harp | Bow | Create Consecrated Ground when you Shatter an Enemy | Utility | `consecrate_ground_on_shatter_%_chance_for_3_seconds` |
| Perandus Signet | Ring | 2% increased Experience gain | Utility | `map_experience_gain_+%` |
| Perandus Signet | Ring | 3% chance for Slain monsters to drop an additional Scroll of Wisdom | Utility | `additional_scroll_of_wisdom_drop_chance_%` |
| Perfidy | Body Armour | (25-50)% increased Valour gained | Utility | `banner_resource_gained_+%` |
| Perfidy | Body Armour | Having a placed Banner does not prevent you gaining Valour | Utility | `base_can_gain_banner_resource`, `can_gain_banner_resource_while_banner_is_placed` |
| Piscator's Vigil | Wand | Cannot roll Caster Modifiers | Utility | `item_generation_cannot_roll_caster_affixes` |
| Primordial Might | Jewel | Summoned Golems are Aggressive | Utility | `golems_larger_aggro_radius` |
| Progenesis | Flask | (-35-35)% reduced Duration | Utility | `local_flask_duration_+%`, `local_flask_consume_flask_duration_+%_when_used` |
| Pure Talent | Jewel | While your Passive Skill Tree connects to a class' starting location, you gain: | Utility | — |
| Quickening Covenant | Jewel | Corrupted | Utility | — |
| Rain of Splinters | Jewel | Corrupted | Utility | — |
| Rapid Expansion | Jewel | With at least 40 Strength in Radius, Ground Slam | Utility | — |
| Rapid Expansion | Jewel | With at least 40 Strength in Radius, Ground Slam has a 35% chance | Utility | — |
| Rapid Expansion | Jewel | has a 50% increased angle | Utility | — |
| Rat's Nest | Helmet | 10% reduced Character Size | Utility | `base_actor_scale_+%` |
| Rational Doctrine | Jewel | Effects of Consecrated Ground you create Linger for 4 seconds | Utility | `your_consecrated_ground_effect_lingers_for_ms_after_leaving_the_area` |
| Rational Doctrine | Jewel | Effects of Profane Ground you create Linger for 4 seconds | Utility | `your_profane_ground_effect_lingers_for_ms_after_leaving_the_area` |
| Reach of the Council | Bow | Arrows fired from the first firing points always Pierce | Utility | `arrows_from_first_firing_point_always_pierce` |
| Reach of the Council | Bow | Arrows fired from the fourth firing points Chain +2 times | Utility | `arrows_from_fourth_firing_point_additional_chains` |
| Reach of the Council | Bow | Arrows fired from the second firing points Fork | Utility | `arrows_from_second_firing_point_fork` |
| Reach of the Council | Bow | Arrows fired from the third firing points Return to you | Utility | `arrows_from_third_firing_point_return` |
| Reclaimed Malevolence | Jewel | Historic | Utility | `local_is_alternate_tree_jewel` |
| Reclaimed Malevolence | Jewel | Passives affected are Conquered by the Abyssal | Utility | — |
| Redblade Banner | Shield | 20% increased Taunt Duration | Utility | `taunt_duration_+%` |
| Redblade Tramplers | Boots | Unaffected by Burning Ground | Utility | `unaffected_by_burning_ground` |
| Reefbane | Fishing Rod | (10-20)% increased Quantity of Fish Caught | Utility | `fish_quantity_+%` |
| Reefbane | Fishing Rod | Glows while in an Area containing a Unique Fish | Utility | `glows_in_area_with_unique_fish` |
| Reefbane | Fishing Rod | Thaumaturgical Lure | Utility | — |
| Relentless Fury | One Handed Axe | You gain Onslaught for 3 seconds on Culling Strike | Utility | `onslaught_buff_duration_on_culling_strike_ms` |
| Remnant of Empires | Shield | Reflects 4 to 8 Physical Damage to Attackers on Block | Utility | `minimum_physical_damage_to_return_on_block`, `maximum_physical_damage_to_return_on_block` |
| Replica Bated Breath | Belt | (20-30)% increased Rarity of Fish Caught | Utility | `fish_rarity_+%` |
| Replica Bated Breath | Belt | 20% increased Fishing Range | Utility | `fishing_range_+%` |
| Replica Bated Breath | Belt | 50% increased Fishing Pool Consumption | Utility | `fishing_pool_consumption_+%` |
| Replica Blood Thorn | Staff | Reflects (22-44) Fire Damage to Attackers on Block | Utility | `fire_damage_to_return_on_block` |
| Replica Bones of Ullr | Boots | Summoned Phantasms have 10% chance to refresh their Duration when they Hit a Rare or Unique Enemy | Utility | `phantasm_refresh_duration_on_hit_vs_rare_or_unique_%_chance` |
| Replica Bones of Ullr | Boots | Summoned Raging Spirits have 10% chance to refresh their Duration when they Hit a Rare or Unique Enemy | Utility | `raging_spirits_refresh_duration_on_hit_vs_rare_or_unique_%_chance` |
| Replica Fragile Bloom | Jewel | Gain up to maximum Fragile Regrowth when Hit | Utility | `gain_up_to_maximum_fragile_regrowth_when_hit` |
| Replica Fragile Bloom | Jewel | Lose 1 Fragile Regrowth each second | Utility | `gain_x_fragile_regrowth_per_second` |
| Replica Fragile Bloom | Jewel | Maximum 5 Fragile Regrowth | Utility | `base_maximum_fragile_regrowth` |
| Replica Headhunter | Belt | 20% chance when you Kill a Magic Monster to gain its Modifiers for 60 seconds | Utility | `gain_magic_monster_mods_on_kill_%_chance` |
| Replica Malachai's Artifice | Ring | All Sockets are White | Utility | `local_all_sockets_are_white` |
| Replica Midnight Bargain | Wand | Cannot be used with Chaos Inoculation | Utility | `local_cannot_be_used_with_chaos_innoculation` |
| Replica Nebulis | Sceptre | (60-120)% increased Implicit Modifier magnitudes | Utility | `local_implicit_stat_magnitude_+%` |
| Replica Primordial Might | Jewel | Summoned Golems are Aggressive | Utility | `golems_larger_aggro_radius` |
| Replica Pure Talent | Jewel | While your Passive Skill Tree connects to a class' starting location, you gain: | Utility | — |
| Replica Sorrow of the Divine | Flask | Creates Consecrated Ground on Use | Utility | `local_consecrate_ground_on_flask_use_radius` |
| Replica Stampede | Boots | This item can be anointed by Cassia | Utility | — |
| Replica Twyzel | Wand | Cannot roll Caster Modifiers | Utility | `item_generation_cannot_roll_caster_affixes` |
| Replica Veil of the Night | Helmet | Reflects 1 to (180-220) Lightning Damage to Attackers on Block | Utility | `minimum_lightning_damage_to_return_on_block`, `maximum_lightning_damage_to_return_on_block` |
| Replica Witchfire Brew | Flask | (-10-10)% reduced Charges per use | Utility | `local_charges_used_+%`, `local_flask_consume_charges_used_+%_when_used` |
| Replica Witchfire Brew | Flask | Creates a Smoke Cloud on Use | Utility | `local_smoke_ground_on_flask_use_radius` |
| Retaliation Charm | Amulet | Blind does not affect your Light Radius | Utility | `blind_does_not_affect_light_radius` |
| Retaliation Charm | Amulet | Blind you inflict is Reflected to you | Utility | `blind_reflected_to_self` |
| Rigwald's Quills | Quiver | Arrows Fork | Utility | `arrows_fork` |
| Sacrificial Harvest | Jewel | (20-30)% chance to gain an additional Vaal Soul on Kill | Utility | `chance_to_gain_vaal_soul_on_kill_%` |
| Sap of the Seasons | Tincture | (35--35)% increased Mana Burn rate | Utility | — |
| Seething Fury | Jewel | Corrupted | Utility | — |
| Serle's Masterwork | One Handed Mace | Can be Enchanted by a Kalguuran Runesmith | Utility | `local_unique_can_be_runesmith_enchanted` |
| Serle's Masterwork | One Handed Mace | Can be Runesmithed as though it were all One Handed Melee Weapon Types | Utility | `local_can_have_any_one_hand_runesmith_enchantments` |
| Serle's Masterwork | One Handed Mace | Can have 2 additional Runesmithing Enchantments | Utility | `local_can_have_X_additional_runesmith_enchantments` |
| Shackles of the Wretched | Gloves | Hexes applied by Socketed Curse Skills are Reflected back to you | Utility | `local_display_socketed_gems_get_curse_reflection` |
| Shadows and Dust | Gloves | Creates a Smoke Cloud on Rampage | Utility | `ground_smoke_on_rampage_threshold_ms` |
| Shadows and Dust | Gloves | Gain Unholy Might for 3 seconds on Rampage | Utility | `gain_unholy_might_on_rampage_threshold_ms` |
| Shattered Chains | Jewel | With at least 40 Strength in Radius, +20% to Rarity of Items dropped by Enemies Shattered by Glacial Hammer | Utility | `local_unique_jewel_glacial_hammer_item_rarity_on_shattering_enemy_+%_with_50_strength_in_radius` |
| Shavronne's Wrappings | Body Armour | Reflects 1 to 250 Lightning Damage to Melee Attackers | Utility | `minimum_lightning_damage_to_return_to_melee_attacker`, `maximum_lightning_damage_to_return_to_melee_attacker` |
| Sibyl's Lament | Ring | Left ring slot: you and your Minions prevent +100% of Reflected Elemental Damage | Utility | `local_left_ring_slot_-%_of_your_elemental_damage_cannot_be_reflected` |
| Sibyl's Lament | Ring | Right ring slot: you and your Minions prevent +100% of Reflected Physical Damage | Utility | `local_right_ring_slot_-%_of_your_physical_damage_cannot_be_reflected` |
| Sin's Rebirth | Flask | Creates a Smoke Cloud on Use | Utility | `local_smoke_ground_on_flask_use_radius` |
| Skin of the Lords | Body Armour | Sockets cannot be modified | Utility | `local_six_linked_random_sockets` |
| Skin of the Loyal | Body Armour | Sockets cannot be modified | Utility | `local_six_linked_random_sockets` |
| Skysunder | Two Handed Sword | Ignites you cause are reflected back to you | Utility | `ignites_reflected_to_self` |
| Solerai's Radiance | Belt | Enemies Blinded by you cannot inflict Damaging Ailments | Utility | `enemies_blinded_by_you_cannot_inflict_damaging_ailments` |
| Song of the Sirens | Fishing Rod | (50-40)% reduced Quantity of Fish Caught | Utility | `fish_quantity_+%` |
| Song of the Sirens | Fishing Rod | (50-60)% increased Rarity of Fish Caught | Utility | `fish_rarity_+%` |
| Song of the Sirens | Fishing Rod | Siren Worm Bait | Utility | — |
| Song of the Sirens | Fishing Rod | You can catch Exotic Fish | Utility | `can_catch_exotic_fish` |
| Soul Ascension | Gloves | +(-10-10) to maximum number of Eaten Souls | Utility | — |
| Soul Ripper | Flask | Consumes Maximum Charges to use | Utility | `local_flask_consumes_max_charges_on_use` |
| Soul Ripper | Flask | Gain Vaal Souls equal to Charges Consumed when used | Utility | `local_flask_gain_charges_consumed_as_vaal_souls_on_use` |
| Soul Ripper | Flask | Loses all Charges when you enter a new area | Utility | `local_flask_lose_all_charges_on_entering_new_area` |
| Soul Taker | One Handed Axe | Insufficient Mana doesn't prevent your Melee Attacks | Utility | `melee_attacks_usable_without_mana_cost` |
| Soul's Wick | Jewel | Corrupted | Utility | — |
| Soul's Wick | Jewel | Raised Spectres have a Base Duration of 20 seconds | Utility | — |
| Soul's Wick | Jewel | Spectres do not travel between Areas | Utility | — |
| Soulbound | Ring | Linked Targets Cannot Die for 2 seconds after you Die | Utility | `link_skill_link_target_cannot_die_for_X_seconds` |
| Soulbound | Ring | Lose no Experience when you die because a Linked target died | Utility | `link_skill_lose_no_experience_on_link_target_death` |
| Soulthirst | Belt | Lose all Eaten Souls when you use a Flask | Utility | `lose_soul_eater_souls_on_flask_use` |
| Southbound | Gloves | Your Hits can only Kill Frozen Enemies | Utility | `hits_can_only_kill_frozen_enemies` |
| Spirit Guards | Jewel | With at least 40 Dexterity in Radius, Animate Weapon can Animate up to 20 Ranged Weapons | Utility | `local_unique_jewel_animate_weapon_can_animate_up_to_x_additional_ranged_weapons_with_50_dex_in_radius` |
| Sporeguard | Body Armour | This item can be anointed by Cassia | Utility | — |
| Squirming Terror | Ring | An Enemy Writhing Worm spawns every 2 seconds | Utility | `local_display_summon_writhing_worm_every_2000_ms` |
| Stasis Prison | Body Armour | (80-100)% increased Implicit Modifier magnitudes | Utility | `local_implicit_stat_magnitude_+%` |
| Steelworm | Quiver | Grants Call of Steel | Utility | — |
| Steppan Eard | Boots | Unaffected by Desecrated Ground | Utility | `unaffected_by_desecrated_ground` |
| Stranglegasp | Amulet | Can have 3 additional Enchantment Modifiers | Utility | `local_item_can_have_x_additional_enchantments` |
| String of Servitude | Belt | Implicit Modifier magnitudes are tripled | Utility | `local_implicit_modifier_magnitudes_tripled` |
| Subsume the Source | Helmet | (120-240)% increased Explicit Modifier magnitudes | Utility | `local_explicit_mod_effect_+%` |
| Subsume the Source | Helmet | One modifier from Consumed Jewels will be retained | Utility | — |
| Subsume the Source | Helmet | Socketed Rare Abyssal Jewels will be Consumed | Utility | — |
| Survival Instincts | Jewel | Survival | Utility | `local_is_survival_jewel` |
| Survival Secrets | Jewel | Flasks gain 3 Charges every 3 seconds while they are inactive | Utility | `flasks_gain_x_charges_while_inactive_every_3_seconds` |
| Survival Secrets | Jewel | Survival | Utility | `local_is_survival_jewel` |
| Survival Skills | Jewel | Survival | Utility | `local_is_survival_jewel` |
| Tawhanuku's Timing | Ring | Cost every third time you Pay it | Utility | — |
| Temptation Step | Boots | Poison you inflict with Travel Skills is Reflected to you if you | Utility | — |
| The Anvil | Amulet | Reflects 240 to 300 Physical Damage to Attackers on Block | Utility | `minimum_physical_damage_to_return_on_block`, `maximum_physical_damage_to_return_on_block` |
| The Bandit Lord's Band | Ring | (25-35)% increased Quantity of Gold Dropped by Slain Enemies | Utility | `item_found_gold_+%` |
| The Battle Within | Tincture | Does not inflict Mana Burn over time | Utility | — |
| The Blood Thorn | Staff | Reflects (22-44) Physical Damage to Attackers on Block | Utility | `minimum_physical_damage_to_return_on_block`, `maximum_physical_damage_to_return_on_block` |
| The Covetous Dark | Claw | Blind you inflict is permanent | Utility | `inflict_permanent_blind` |
| The Covetous Dark | Claw | Blinding a non-Blinded Pinnacle Atlas Boss with this Weapon will | Utility | — |
| The Covetous Dark | Claw | steal a Modifier for this item (2 Modifiers remaining) | Utility | — |
| The Dancing Dervish | Two Handed Sword | Manifested Dancing Dervishes die when Rampage ends | Utility | `local_display_manifest_dancing_dervish_destroy_on_end_rampage` |
| The Dancing Dervish | Two Handed Sword | Manifested Dancing Dervishes disables both weapon slots | Utility | `local_display_manifest_dancing_dervish_disables_weapons` |
| The Dancing Dervish | Two Handed Sword | Melee Hits count as Rampage Kills | Utility | — |
| The Dancing Duo | Two Handed Sword | Manifested Dancing Dervishes die when Rampage ends | Utility | `local_display_manifest_dancing_dervish_destroy_on_end_rampage` |
| The Dancing Duo | Two Handed Sword | Manifested Dancing Dervishes disables both weapon slots | Utility | `local_display_manifest_dancing_dervish_disables_weapons` |
| The Dancing Duo | Two Handed Sword | Melee Hits count as Rampage Kills | Utility | — |
| The Fulcrum | Staff | Elemental Ailments you inflict are Reflected to you | Utility | `elemental_ailments_reflected_to_self` |
| The Geomantic Gyre | Staff | Crucible Passive Skill Tree is removed if this Modifier is removed | Utility | — |
| The Goddess Unleashed | One Handed Sword | 20% increased Attack and Movement Speed with Her Blessing | Utility | `attack_and_movement_speed_+%_with_her_blessing` |
| The Goddess Unleashed | One Handed Sword | 33% chance to Blind Enemies within 1.2 metres when gaining Her Blessing | Utility | `blind_nearby_enemies_when_gaining_her_blessing_%` |
| The Golden Rule | Jewel | Bleeding you inflict is Reflected to you | Utility | `bleeding_reflected_to_self` |
| The Golden Rule | Jewel | Corrupted | Utility | — |
| The Golden Rule | Jewel | Poison you inflict is Reflected to you if you have fewer than 100 Poisons on you | Utility | `poison_reflected_to_self` |
| The Grey Spire | Staff | Implicit Modifier magnitudes are doubled | Utility | `local_implicit_modifier_magnitudes_doubled` |
| The Grey Wind | One Handed Axe | +(-5-5) to Maximum Rage | Utility | — |
| The Iron Mass | One Handed Sword | Summoned Skeleton Warriors and Soldiers wield this Weapon while in your Main Hand | Utility | `summoned_skeleton_warriors_get_weapon_stats_in_main_hand` |
| The Living Blade | Two Handed Sword | 10% chance to remove 1 Mana Burn on Kill | Utility | `chance_to_remove_1_tincture_toxicity_on_kill_%` |
| The Long Winter | Jewel | With 40 Intelligence in Radius, Glacial Cascade has an additional Burst | Utility | `local_unique_jewel_glacial_cascade_number_of_additional_bursts_with_40_int_in_radius` |
| The Overflowing Chalice | Flask | (50-100)% increased Charges gained by Other Flasks during Effect | Utility | `local_unique_flask_charges_gained_+%_during_flask_effect` |
| The Overflowing Chalice | Flask | Creates Consecrated Ground on Use | Utility | `local_consecrate_ground_on_flask_use_radius` |
| The Overflowing Chalice | Flask | Gains no Charges during Effect of any Overflowing Chalice Flask | Utility | `local_unique_overflowing_chalice_flask_cannot_gain_flask_charges_during_flask_effect` |
| The Poet's Pen | Wand | Cannot roll Caster Modifiers | Utility | `item_generation_cannot_roll_caster_affixes` |
| The Primordial Chain | Amulet | 25% reduced Golem Size | Utility | `golem_scale_+%` |
| The Redblade | One Handed Sword | Crucible Passive Skill Tree is removed if this Modifier is removed | Utility | — |
| The Redblade | One Handed Sword | Has a Two Handed Sword Crucible Passive Skill Tree | Utility | — |
| The Sorrow of the Divine | Flask | Creates Consecrated Ground on Use | Utility | `local_consecrate_ground_on_flask_use_radius` |
| The Stampede | Boots | This item can be anointed by Cassia | Utility | — |
| The Supreme Truth | Sceptre | 3% increased Experience gain | Utility | `map_experience_gain_+%` |
| The Trickster's Smile | Helmet | Reflects 100 Cold Damage to Melee Attackers | Utility | `cold_damage_to_return_to_melee_attacker` |
| The Trickster's Smile | Helmet | Reflects 100 Fire Damage to Melee Attackers | Utility | `fire_damage_to_return_to_melee_attacker` |
| The Trickster's Smile | Helmet | Reflects 100 Lightning Damage to Melee Attackers | Utility | `lightning_damage_to_return_to_melee_attacker` |
| The Untouched Soul | Amulet | Players have +40 to maximum Mana for each Empty Blue Socket on any Equipped Item | Utility | `maximum_mana_+_per_empty_blue_socket` |
| The Untouched Soul | Amulet | on any Equipped Item | Utility | — |
| The Writhing Jar | Flask | 2 Enemy Writhing Worms escape the Flask when used | Utility | — |
| The Writhing Jar | Flask | Writhing Worms are destroyed when Hit | Utility | — |
| Thousand Teeth Temu | Shield | Reflects 1000 to 10000 Physical Damage to Attackers on Block | Utility | `minimum_physical_damage_to_return_on_block`, `maximum_physical_damage_to_return_on_block` |
| Thread of Hope | Jewel | Passage | Utility | — |
| To Dust | Jewel | Corrupted | Utility | — |
| Torchoak Step | Boots | Totems Reflect 100% of their maximum Life as Fire Damage to Enemies within 1.8 metres when Hit | Utility | `totem_%_maximum_life_inflicted_as_aoe_fire_damage_when_hit` |
| Twyzel | Wand | Cannot roll Caster Modifiers | Utility | `item_generation_cannot_roll_caster_affixes` |
| Ulaman's Gaze | Jewel | Searching Eye Jewel affecting you, up to a maximum of 20% | Utility | — |
| Vaal Caress | Gloves | You gain Onslaught for 20 seconds on using a Vaal Skill | Utility | `onslaught_on_vaal_skill_use_duration_ms` |
| Veil of Flesh | Helmet | Gain Bitterblood equal to Life spent | Utility | `flesh_barrier_gain_from_life_spent_%` |
| Veil of the Night | Helmet | Reflects 1 to (180-220) Lightning Damage to Attackers on Block | Utility | `minimum_lightning_damage_to_return_on_block`, `maximum_lightning_damage_to_return_on_block` |
| Venarius' Astrolabe | Amulet | Has Elder, Shaper and all Conqueror Influences | Utility | `local_item_can_roll_all_influences` |
| Venarius' Astrolabe | Amulet | Implicit Modifiers Cannot Be Changed | Utility | `local_implicit_mod_cannot_be_changed` |
| Ventor's Gamble | Ring | +(-40-40)% to Item Rarity | Utility | — |
| Veruso's Ambition | Boots | Enemies display their Monster Category | Utility | `can_see_corpse_types` |
| Vestige of Divinity | Staff | Reflects 8 to 14 Physical Damage to Attackers on Block | Utility | `minimum_physical_damage_to_return_on_block`, `maximum_physical_damage_to_return_on_block` |
| Violent Dead | Jewel | With at least 40 Intelligence in Radius, Raised | Utility | — |
| Voidfletcher | Quiver | 5 Maximum Void Charges | Utility | `maximum_void_arrows` |
| Voidfletcher | Quiver | Gain a Void Charge every second | Utility | `grant_void_arrow_every_x_ms` |
| Voidheart | Ring | 10% chance to Cause Monsters to Flee | Utility | `local_hit_causes_monster_flee_%` |
| Voidhome | Two Handed Mace | (30-50)% reduced Experience gain | Utility | `experience_gain_+%` |
| Vorana's Preparation | Flask | (-10-10)% reduced Charges per use | Utility | `local_charges_used_+%`, `local_flask_consume_charges_used_+%_when_used` |
| Wall of Brambles | Body Armour | 40% of Melee Physical Damage taken reflected to Attacker | Utility | `melee_physical_damage_taken_%_to_deal_to_attacker` |
| Watcher's Eye | Jewel | (30-50)% chance to Blind Enemies which Hit you while affected by Grace | Utility | `blind_enemies_when_hit_while_affected_by_grace_%_chance` |
| Wine of the Prophet | Flask | Grants a random Divination Buff for 20 seconds when Used | Utility | `divination_buff_on_flask_used_duration_cs` |
| Winter Burial | Jewel | With at least 40 Strength in Radius, Glacial Hammer deals | Utility | — |
| Witchfire Brew | Flask | (-10-10)% reduced Charges per use | Utility | `local_charges_used_+%`, `local_flask_consume_charges_used_+%_when_used` |
| Witchfire Brew | Flask | Creates a Smoke Cloud on Use | Utility | `local_smoke_ground_on_flask_use_radius` |
| Xirgil's Crank | Staff | Reflects 1 to 150 Lightning Damage to Melee Attackers | Utility | `minimum_lightning_damage_to_return_to_melee_attacker`, `maximum_lightning_damage_to_return_to_melee_attacker` |
| Xoph's Blood | Amulet | Cover Enemies in Ash when they Hit you | Utility | `apply_covered_in_ash_to_attacker_when_hit_%` |
| Zerphi's Last Breath | Flask | Grants Last Breath when you Use a Skill during Effect, for (450-600)% of Mana Cost | Utility | `local_flask_life_gain_on_skill_use_%_mana_cost` |
|  Death Offering | Catarina | Offerings Kill affected Damagable targets when Offering Duration expires | Utility | `offerings_kill_affected_damagable_targets_when_offering_duration_expires` |
| Afarud Ritual | Necromantic | up to a maximum of 150% | Utility | — |
| Afarud Ritual | Necromantic | up to a maximum of 50% | Utility | — |
| Armour and Evasion, Taunt Duration | Champion | 20% increased Taunt Duration | Utility | `taunt_duration_+%` |
| Avatar of the Wilds | Raider | Cannot gain Unbound Fury while Unbound | Utility | — |
| Banner Valour Gained | Normal | 20% increased Valour gained | Utility | `banner_resource_gained_+%` |
| Banner Valour Gained | Normal | 20% increased Valour gained | Utility | `banner_resource_gained_+%` |
| Banner Valour Gained | Normal | 20% increased Valour gained | Utility | `banner_resource_gained_+%` |
| Banner Valour Gained | Normal | 20% increased Valour gained | Utility | `banner_resource_gained_+%` |
| Banner Valour Gained | Normal | 20% increased Valour gained | Utility | `banner_resource_gained_+%` |
| Blind Duration | Normal | 40% increased Blind duration | Utility | `blind_duration_+%` |
| Bloodsoaked Blade | Keystone | Effects that interact with Mana Burn interact with Weeping Wounds instead | Utility | — |
| Bound Flesh | Necromantic | Gain 20 Baryatic Tension per 20 Life Spent on Upfront Costs of Spells | Utility | `gain_x_blood_phylactery_per_20_life_spent_on_upfront_cost_of_spells` |
| Chain Distance | Normal | 15% increased Chaining range | Utility | `chaining_range_+%` |
| Corruption's Embrace | Trialmaster | You have Sacrifice of Blood if at least 8 Corrupted Items are Equipped | Utility | `keystone_sacrifice_of_blood_if_at_least_8_corrupted_items_equipped` |
| Defy Pain | Berserker | Gain Defiance for 10 seconds on losing Life to an Enemy Hit, no | Utility | — |
| Defy Pain | Berserker | Lose all Defiance when you reach 10 Defiance | Utility | `lose_all_defiance_on_reaching_x_defiance` |
| Disorienting Display | Notable | 10% chance to Blind Enemies within 6 metres when you use an Elemental Skill | Utility | `elemental_skill_chance_to_blind_nearby_enemies_%` |
| Farric Will | Farrul | Raised Beast Spectres have 3 additional modifiers randomly chosen in each Area | Utility | `raised_beast_spectres_have_x_random_modifiers_per_area` |
| Fearsome Warrior | Notable | 25% chance to Intimidate Enemies within 4 metres for 4 seconds on Melee Kill | Utility | `chance_to_intimidate_nearby_enemies_on_melee_kill_%` |
| Fertile Will | Farrul | Raised Beast Spectres have 3 additional modifiers randomly chosen in each Area | Utility | `raised_beast_spectres_have_x_random_modifiers_per_area` |
| Fire Attunement | Notable | Unaffected by Burning Ground | Utility | `unaffected_by_burning_ground` |
| First to Strike, Last to Fall | Champion | Gain Adrenaline for 20 seconds when you reach Low Life | Utility | `gain_adrenaline_for_X_seconds_on_low_life_unless_you_have_adrenaline` |
| Flask Charges against Marked Enemy | Normal | Marked Enemy grants 20% increased Flask Charges to you | Utility | `flask_charges_gained_from_marked_enemy_+%` |
| Flask Charges against Marked Enemy | Normal | Marked Enemy grants 20% increased Flask Charges to you | Utility | `flask_charges_gained_from_marked_enemy_+%` |
| Focal Point | Deadeye | Your Mark Transfers to another Enemy within 3 metres when Marked Enemy dies | Utility | `your_marks_transfer_to_nearby_enemies_on_death_%_chance` |
| Fury of Nature | Raider | Non-Damaging Elemental Ailments you inflict spread to nearby enemies within 2 metres | Utility | — |
| Ghost Dance | Keystone | Every 2 seconds, gain a Ghost Shroud, up to a maximum of 3 | Utility | — |
| Golden Glory | Luminary | Increases and Reductions to Light Radius also apply to Effect of | Utility | — |
| Golden Glory | Luminary | your Link Skill Buffs on your Mercenary at 50% of their value | Utility | — |
| Heartstopper | Trickster | Every 10 seconds: | Utility | — |
| Inquisitor | Ascendant | 10% chance to create Consecrated Ground when you Hit a Rare or Unique Enemy, lasting 8 seconds | Utility | `create_consecrated_ground_on_hit_%_vs_rare_or_unique_enemy` |
| Inquisitor | Ascendant | Effects of Consecrated Ground you create Linger for 4 seconds | Utility | `your_consecrated_ground_effect_lingers_for_ms_after_leaving_the_area` |
| Instruments of Zeal | Inquisitor | +3 to Maximum Fanatic Charges | Utility | `maximum_fanaticism_charges` |
| Instruments of Zeal | Inquisitor | Gain 1 Fanatic Charge every second if you've Attacked in the past second | Utility | `gain_x_fanatic_charges_every_second_if_have_attacked_in_past_second` |
| Instruments of Zeal | Inquisitor | Lose all Fanatic Charges on reaching Maximum Fanatic Charges | Utility | `lose_all_fanatic_charges_on_reaching_maximum_fanatic_charges` |
| Legendary Amulets | Luminary | Your Mercenary can equip Unique Amulets | Utility | `mercenary_can_use_unique_amulet` |
| Legendary Arms | Luminary | Your Mercenary can equip Unique Weapons, Shields and Quivers | Utility | `mercenary_can_use_unique_weapons_shields_and_quivers` |
| Legendary Arms | Luminary | each Unique item they have equipped | Utility | — |
| Legendary Belts | Luminary | Your Mercenary can equip Unique Belts | Utility | `mercenary_can_use_unique_belt` |
| Legendary Boots | Luminary | Your Mercenary can equip Unique Boots | Utility | `mercenary_can_use_unique_boots` |
| Legendary Gloves | Luminary | Your Mercenary can equip Unique Gloves | Utility | `mercenary_can_use_unique_gloves` |
| Legendary Helmets | Luminary | Your Mercenary can equip Unique Helmets | Utility | `mercenary_can_use_unique_helmet` |
| Legendary Rings | Luminary | Your Mercenary can equip Unique Rings | Utility | `mercenary_can_use_unique_ring` |
| Liege of the Primordial | Elementalist | Summoned Golems are Resummoned 4 seconds after being Killed | Utility | `revive_golems_if_killed_by_enemies_ms` |
| Lone Messenger | Keystone | You can only have one Herald | Utility | — |
| Master Surgeon | Pathfinder | Life Flask Effects do not Queue | Utility | — |
| Nature's Concoction | Notable | Flasks adjacent to active Tinctures gain 2 charges when you Hit an | Utility | — |
| Noble Blood | Luminary | You can hire a Mercenary permanently | Utility | `can_have_active_mercenary_follower` |
| Oath of Fealty | Luminary | If your Linked Mercenary dies, the Link owner does not also die | Utility | `objects_linked_to_your_permanenet_mercenaries_do_not_die_when_they_die` |
| Occupying Force | Deadeye | Cannot Summon Mirage Archers while near your Mirage Archers | Utility | `cannot_summon_mirage_archer_if_near_mirage_archer_radius` |
| Occupying Force | Deadeye | Mirage Archers are not attached to you | Utility | `mirage_archers_do_not_attach` |
| Path of the Duelist | Ascendant | Can Allocate Passives from the Duelist's starting point | Utility | — |
| Path of the Marauder | Ascendant | Can Allocate Passives from the Marauder's starting point | Utility | — |
| Path of the Ranger | Ascendant | Can Allocate Passives from the Ranger's starting point | Utility | — |
| Path of the Shadow | Ascendant | Can Allocate Passives from the Shadow's starting point | Utility | — |
| Path of the Templar | Ascendant | Can Allocate Passives from the Templar's starting point | Utility | — |
| Path of the Witch | Ascendant | Can Allocate Passives from the Witch's starting point | Utility | — |
| Pious Path | Inquisitor | Effects of Consecrated Ground you create Linger for 4 seconds | Utility | `your_consecrated_ground_effect_lingers_for_ms_after_leaving_the_area` |
| Pitfighter | Keystone | 1% increased Fishing Line Strength | Utility | `fishing_line_strength_+%` |
| Powerful Bond | Notable | 20% increased Buff Effect of your Links for which 50% of Link Duration has Expired | Utility | `link_effect_+%_when_50%_expired` |
| Prepared Response | Notable | 25% chance when you use a Retaliation Skill for a different Retaliation Skill to become Usable | Utility | `gain_random_retaliation_requirement_on_retaliation_used_chance_%` |
| Purposeful Harbinger | Notable | each Herald affecting you, up to a maximum of 40% | Utility | — |
| Righteous Fury | Notable | 10% chance to create Consecrated Ground on Melee Kill, lasting 4 seconds | Utility | `chance_to_create_consecrated_ground_on_melee_kill_%` |
| Seeker Runes | Notable | second, up to a maximum of 100% | Utility | — |
| Smoking Remains | Notable | 10% chance to create a Smoke Cloud on Kill | Utility | `create_smoke_cloud_on_kill_%_chance` |
| Spiked Bulwark | Notable | Reflects 50 Physical Damage to Melee Attackers | Utility | `physical_damage_to_return_to_melee_attacker` |
| That didn't happen! | Delirious | Non-Cluster, Non-Passage, Non-Mycelium Jewels Socketed in your Passive Skill Tree have no effect | Utility | `socketed_non_cluster_jewels_have_no_effect` |
| The Living Blade | Reliquarian | 10% chance to remove 1 Mana Burn on Kill | Utility | `chance_to_remove_1_tincture_toxicity_on_kill_%` |
| Tide Caller | Brinerot | Grants Level 20 Surging Torrent | Utility | — |
| Trick Shot | Notable | 30% increased Chaining range | Utility | `chaining_range_+%` |
| Undertaker | Notable | Desecrate and Unearth have +2 to Maximum number of corpses allowed | Utility | `desecrate_maximum_number_of_corpses` |
| Vaal Souls | Trialmaster | Gain 1 Vaal Soul per second | Utility | `vaal_souls_gained_per_minute` |
| Vanquisher | Notable | Crush Enemies for 4 seconds when you Hit them while they are on Full Life | Utility | `crush_on_hit_ms_vs_full_life_enemies` |
| Vinespike Cordial | Notable | 8 Grasping Vines during Effect of any Life Flask | Utility | — |
| Volatile Presence | Notable | 20% increased Duration of Fire Ailments | Utility | `fire_ailment_duration_+%` |
| Wild Will | Farrul | Raised Beast Spectres have 3 additional modifiers randomly chosen in each Area | Utility | `raised_beast_spectres_have_x_random_modifiers_per_area` |
| Wind Ward | Deadeye | Lose all Gale Force when Hit | Utility | `lose_all_gale_force_when_hit` |
| Worthy Causes | Champion | Having a placed Banner does not prevent you gaining Valour | Utility | `base_can_gain_banner_resource`, `can_gain_banner_resource_while_banner_is_placed` |

## Unsupported · Cosmetic (16)

| Source | Where | Line | Impact | Game stat id |
|---|---|---|---|---|
| Abberath's Hooves | Boots | Burning Hoofprints | Cosmetic | `goat_footprints_from_item` |
| Belly of the Beast | Body Armour | Extra gore | Cosmetic | `extra_gore` |
| Bloodplay | Dagger | Extra gore | Cosmetic | `extra_gore` |
| Carcass Jack | Body Armour | Extra gore | Cosmetic | `extra_gore` |
| Carnage Heart | Amulet | Extra gore | Cosmetic | `extra_gore` |
| Death's Oath | Body Armour | Gore Footprints | Cosmetic | `blood_footprints_from_item` |
| Devoto's Devotion | Helmet | Mercury Footprints | Cosmetic | `silver_footprints_from_item` |
| Facebreaker | Gloves | Extra gore | Cosmetic | `extra_gore` |
| Gorebreaker | One Handed Mace | Extra gore | Cosmetic | `extra_gore` |
| Replica Bloodplay | Dagger | Extra gore | Cosmetic | `extra_gore` |
| Replica Red Trail | Boots | Necrotic Footprints | Cosmetic | `necrotic_footprints_from_item` |
| Replica Voidwalker | Boots | Celestial Footprints | Cosmetic | `celestial_footprints_from_item` |
| The Blood Dance | Boots | Gore Footprints | Cosmetic | `blood_footprints_from_item` |
| The Bringer of Rain | Helmet | Extra gore | Cosmetic | `extra_gore` |
| The Red Trail | Boots | Gore Footprints | Cosmetic | `blood_footprints_from_item` |
| Voidwalker | Boots | Celestial Footprints | Cosmetic | `celestial_footprints_from_item` |
