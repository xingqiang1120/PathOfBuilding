describe("TestModCoverage", function()
	before_each(function()
		newBuild()
	end)

	it("maps display lines to official stat ids", function()
		assert.are.same({ "blood_footprints_from_item" }, modCoverage.FindStatIds("Gore Footprints"))
		-- Ranges are collapsed before matching
		assert.are.same({ "banner_resource_gained_+%" }, modCoverage.FindStatIds("(25-50)% increased Valour gained"))
		assert.is_nil(modCoverage.FindStatIds("This line does not exist in the game"))
	end)

	it("classifies supported and unsupported lines", function()
		local line = "+10 to maximum Life"
		local supported = modCoverage.ClassifyLine(line, modLib.parseMod(line))
		assert.are.equal("supported", supported.status)
		assert.is_nil(supported.impact)

		line = "Gore Footprints"
		local unsupported = modCoverage.ClassifyLine(line, modLib.parseMod(line))
		assert.are.equal("unsupported", unsupported.status)
		assert.are.equal("cosmetic", unsupported.impact)
	end)

	it("estimates impact", function()
		assert.are.equal("offence", modCoverage.EstimateImpact("Withered does not expire on Enemies Ignited by you"))
		assert.are.equal("defence", modCoverage.EstimateImpact("You take 10% reduced Damage from Hits"))
		assert.are.equal("utility", modCoverage.EstimateImpact("1000% of Melee Physical Damage taken reflected to Attacker"))
		assert.are.equal("cosmetic", modCoverage.EstimateImpact("Extra gore"))
		-- "on your" must not count as "on you"
		assert.is_true(modCoverage.EstimateImpact("Buffs on your Mercenary") ~= "defence")
	end)

	it("scans the passive tree", function()
		local entries = modCoverage.ScanTree(build.spec.tree)
		local unsupported = 0
		for _, e in ipairs(entries) do
			assert.are.equal("node", e.kind)
			if e.status == "unsupported" then
				unsupported = unsupported + 1
				assert.is_truthy(e.impact)
			end
		end
		assert.is_true(#entries > 1000)
		assert.is_true(unsupported > 0)
	end)

	it("scans what a build uses", function()
		local item = new("Item"):Item("Rarity: UNIQUE\nCoverage Test Boots\nIron Greaves\nGore Footprints\n+10 to maximum Life")
		build.itemsTab:AddItem(item, true)
		build.itemsTab.slots["Boots"]:SetSelItemId(item.id)
		build.itemsTab:PopulateSlots()
		runCallback("OnFrame")

		local found = { }
		for _, e in ipairs(modCoverage.ScanBuild(build)) do
			if e.source == "Coverage Test Boots" then
				found[e.line] = e
			end
		end
		assert.are.equal("supported", found["+10 to maximum Life"].status)
		assert.are.equal("unsupported", found["Gore Footprints"].status)
		assert.are.equal("Boots", found["Gore Footprints"].detail)
	end)

	it("diffs reports", function()
		local old = {
			{ kind = "node", source = "A", line = "fixed line", status = "unsupported" },
			{ kind = "node", source = "B", line = "still missing", status = "unsupported" },
		}
		local new = {
			{ kind = "node", source = "A", line = "fixed line", status = "supported" },
			{ kind = "node", source = "B", line = "still missing", status = "unsupported" },
			{ kind = "node", source = "C", line = "new line", status = "unsupported" },
		}
		local diff = modCoverage.Diff(old, new)
		assert.are.equal(1, #diff.added)
		assert.are.equal("new line", diff.added[1].line)
		assert.are.equal(1, #diff.fixed)
		assert.are.equal("fixed line", diff.fixed[1].line)
	end)

	it("builds JSON and Markdown reports", function()
		local entries = {
			{ kind = "unique", source = "X", detail = "Boots", line = "Gore Footprints", status = "unsupported", impact = "cosmetic", statIds = { "blood_footprints_from_item" } },
			{ kind = "unique", source = "X", detail = "Boots", line = "+10 to maximum Life", status = "supported" },
		}
		local report = modCoverage.BuildReport(entries, { title = "Test" })
		assert.are.equal(2, report.summary.unique.lines)
		assert.are.equal(1, report.summary.unique.unsupported)
		assert.are.equal(1, report.summary.unique.mapped)
		local json = modCoverage.ToJSONTable(report)
		assert.are.equal(1, #json.unsupported)
		local md = modCoverage.ToMarkdown(report)
		assert.is_truthy(md:find("## Summary", 1, true))
		assert.is_truthy(md:find("blood_footprints_from_item", 1, true))
	end)
end)
