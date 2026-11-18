describe("TestAutoTags", function()
	before_each(function()
		newBuild()
	end)

	local savedUserFilePath = autoTags.userFilePath

	after_each(function()
		-- Drop any overrides and user tags added by a test
		autoTags.Init(LoadModule("Data/AutoTagRules"), LoadModule("Data/AutoTagOverrides"))
		autoTags.userFilePath = savedUserFilePath
		while main.popups[1] do
			main:ClosePopup()
		end
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

	it("derives minion type sub-tags that imply minion", function()
		local tags = lineTags("+1 to maximum number of Raised Zombies")
		assert.is_true(tags.zombie)
		assert.is_true(tags.minion)
		local baron = autoTags.GetItemTags(findUnique("The Baron"))
		assert.is_true(baron.zombie)
		-- Spider's Web is a player skill effect, not a spider minion
		assert.is_nil(autoTags.GetItemTags(findUnique("Fenumus' Shroud")).spider)
	end)

	it("lists sub-tags right after their parent", function()
		local list = autoTags.GetTagList()
		for i, def in ipairs(list) do
			if def.id == "minion" then
				assert.are.equal("zombie", list[i + 1].id)
				assert.are.equal(1, list[i + 1].depth)
				return
			end
		end
		error("minion tag not found")
	end)

	it("parses editor input into user tags", function()
		local add, remove = autoTags.ParseEditString("Minion/My Zombie Build, SRS, -Life, -unknowntag")
		assert.are.same({ "myzombiebuild", "srs" }, add)
		assert.are.same({ "life" }, remove)
		assert.are.equal("minion", autoTags.GetTagDef("myzombiebuild").parent)
		assert.is_true(autoTags.GetTagDef("srs").user)

		autoTags.SetUserEntry("item", "Kaom's Heart", add, remove)
		local tags = autoTags.GetItemTags(findUnique("Kaom's Heart"))
		assert.is_true(tags.myzombiebuild)
		assert.is_true(tags.minion)
		assert.is_true(tags.srs)
		assert.is_nil(tags.life)
		assert.are.equal("Minion/My Zombie Build, SRS, -Life", autoTags.FormatEditString("item", "Kaom's Heart"))
	end)

	it("applies user tags to passive nodes and refreshes cached tags", function()
		local node = findNode("Ravenous Horde")
		assert.is_nil(autoTags.GetNodeTags(node).srs)
		local add = autoTags.ParseEditString("SRS")
		autoTags.SetUserEntry("node", node.id, add, { })
		assert.is_true(autoTags.GetNodeTags(node).srs)

		local viewer = build.treeTab.viewer
		viewer.searchParams = { "tag:srs" }
		assert.is_true(viewer:DoesNodeMatchSearchParams(node))
	end)

	it("saves and loads user tags", function()
		local path = os.tmpname()
		local node = findNode("Ravenous Horde")
		autoTags.SetUserEntry("item", "The Baron", autoTags.ParseEditString("Minion/My Zombie Build, -Life"))
		autoTags.SetUserEntry("node", node.id, autoTags.ParseEditString("Strength Stacking"), { })
		autoTags.SetUserEntryName("node", node.id, node.dn)
		assert.is_truthy(autoTags.SaveUserFile(path))

		autoTags.Init(LoadModule("Data/AutoTagRules"), LoadModule("Data/AutoTagOverrides"))
		assert.is_nil(autoTags.GetTagDef("myzombiebuild"))
		autoTags.LoadUserFile(path)
		os.remove(path)

		assert.are.equal("minion", autoTags.GetTagDef("myzombiebuild").parent)
		local baron = autoTags.GetItemTags(findUnique("The Baron"))
		assert.is_true(baron.myzombiebuild)
		assert.is_nil(baron.life)
		assert.is_true(autoTags.GetNodeTags(node).strengthstacking)
	end)

	it("edits tags through the popup and refreshes the item DB filter", function()
		local path = os.tmpname()
		autoTags.userFilePath = path
		local db = build.itemsTab.controls.uniqueDB
		autoTagEditor.OpenForItem(findUnique("Kaom's Heart"))
		local popup = main.popups[1]
		assert.is_truthy(popup)
		popup.controls.edit:SetText("Tanky Stuff")
		popup.controls.save.onClick()
		os.remove(path)
		assert.is_nil(main.popups[1])
		assert.is_true(autoTags.GetItemTags(findUnique("Kaom's Heart")).tankystuff)

		db:RefreshTagList()
		db.controls.tag:SelByValue("tankystuff", "tagId")
		assert.are.equal("tankystuff", db.tagList[db.controls.tag.selIndex].tagId)
		local matches = 0
		for _, item in pairs(db.db.list) do
			if db:DoesItemMatchFilters(item) then
				matches = matches + 1
			end
		end
		assert.are.equal(1, matches)
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
