describe("TestMercenary", function()
	before_each(function()
		newBuild()
	end)

	local bodyguard = "If your Mercenary's Life is higher than your own, 20% of Damage from Hits is taken from your Mercenary's Life before you"

	local function calc(mercLife)
		build.configTab.input.customMods = bodyguard
		build.configTab.input.TotalMercenaryLife = mercLife
		build.configTab:BuildModList()
		runCallback("OnFrame")
		return build.calcsTab.mainOutput
	end

	it("parses Loyal Bodyguard", function()
		local list, extra = modLib.parseMod(bodyguard)
		assert.is_nil(extra)
		assert.are.equal("takenFromMercenaryBeforeYou", list[1].name)
		assert.are.equal(20, list[1].value)
	end)

	it("takes hit damage from the mercenary only while its Life is higher than yours", function()
		local base = calc(nil)
		assert.are.equal(0, base.MercenaryAllyDamageMitigation or 0)
		local lower = calc(1)
		assert.are.equal(0, lower.MercenaryAllyDamageMitigation)
		assert.are.equal(base.PhysicalMaximumHitTaken, lower.PhysicalMaximumHitTaken)
		local higher = calc(1000000)
		assert.are.equal(20, higher.MercenaryAllyDamageMitigation)
		-- 20% of each hit goes to the mercenary, so the largest survivable hit is 1 / 0.8 times larger
		assert.is_true(math.abs(higher.PhysicalMaximumHitTaken - base.PhysicalMaximumHitTaken / 0.8) <= 2)
	end)
end)
