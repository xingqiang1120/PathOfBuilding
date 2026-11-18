describe("TestAutoTags", function()
	before_each(function()
		newBuild()
	end)

	after_each(function()
		-- Drop any overrides added by a test
		autoTags.Init(LoadModule("Data/AutoTagRules"), LoadModule("Data/AutoTagOverrides"))
	end)

	local function lineTags(line)
		local modList, extra = modLib.parseMod(line)
		return autoTags.GetLineTags(modList, extra, line)
	end

	local function findUnique(title)
		for _, item in pairs(main.uniqueDB.list) do
			if item.title == title then
				return item
			end
		end
	end

	local function findNode(name)
		for _, node in pairs(build.spec.nodes) do
			if node.dn == name then
				return node
			end
		end
	end

	it("tags player modifiers by damage type", function()
		local tags = lineTags("20% increased Fire Damage")
		assert.is_true(tags.fire)
		assert.is_nil(tags.minion)
	end)

	it("tags minion modifiers only as minion", function()
		local tags = lineTags("Minions deal 20% increased Fire Damage")
		assert.is_true(tags.minion)
		assert.is_nil(tags.fire)
	end)

	it("separates minion limits from totem limits", function()
		local skeletons = lineTags("+1 to maximum number of Skeletons")
		assert.is_true(skeletons.minion)
		local totems = lineTags("+1 to maximum number of Summoned Totems")
		assert.is_true(totems.totem)
		assert.is_nil(totems.minion)
	end)

	it("tags gem level modifiers by gem keyword", function()
		assert.is_true(lineTags("+1 to Level of all Minion Skill Gems").minion)
	end)

	it("does not tag resistances as elemental damage", function()
		local tags = lineTags("+30% to Fire Resistance")
		assert.is_true(tags.resistance)
		assert.is_nil(tags.fire)
	end)

	it("falls back to line text for unparsed modifiers", function()
		local tags = autoTags.GetLineTags({ }, "unparsed", "Your Minions are made of jelly")
		assert.is_true(tags.minion)
	end)

	it("tags unique items", function()
		local baron = findUnique("The Baron")
		assert.is_truthy(baron)
		assert.is_true(autoTags.GetItemTags(baron).minion)
		local kaom = findUnique("Kaom's Heart")
		assert.is_truthy(kaom)
		local kaomTags = autoTags.GetItemTags(kaom)
		assert.is_true(kaomTags.life)
		assert.is_nil(kaomTags.minion)
	end)

	it("tags passive nodes and supports tree search", function()
		local node = findNode("Ravenous Horde")
		assert.is_truthy(node)
		assert.is_true(autoTags.GetNodeTags(node).minion)

		local viewer = build.treeTab.viewer
		viewer.searchParams = { "tag:minion" }
		assert.is_true(viewer:DoesNodeMatchSearchParams(node))
		viewer.searchParams = { "tag:totem" }
		assert.is_false(viewer:DoesNodeMatchSearchParams(node))
		viewer.searchParams = { "tag:notatag" }
		assert.is_false(viewer:DoesNodeMatchSearchParams(node))
	end)

	it("resolves tag queries by id or label", function()
		local ids, unknown = autoTags.ParseQuery("Energy Shield, minion")
		assert.are.same({ "energyshield", "minion" }, ids)
		assert.are.same({ }, unknown)
		ids, unknown = autoTags.ParseQuery("energyshield,bogus")
		assert.are.same({ "energyshield" }, ids)
		assert.are.same({ "bogus" }, unknown)
	end)

	it("applies manual overrides with parent tags", function()
		autoTags.AddOverrides({
			tags = { { id = "srs", label = "Summon Raging Spirit", category = "Skill", parent = "minion" } },
			items = { ["Kaom's Heart"] = { add = { "srs" }, remove = { "life" } } },
		})
		local tags = autoTags.GetItemTags(findUnique("Kaom's Heart"))
		assert.is_true(tags.srs)
		assert.is_true(tags.minion)
		assert.is_nil(tags.life)
	end)
end)
