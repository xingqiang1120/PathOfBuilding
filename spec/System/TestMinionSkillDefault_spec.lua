describe("TestMinionSkillDefault", function()
	before_each(function()
		newBuild()
	end)

	local function equipUnique(title, slotName)
		for _, item in pairs(main.uniqueDB.list) do
			if item.title == title then
				local newItem = new("Item"):Item(item.raw)
				build.itemsTab:AddItem(newItem, true)
				build.itemsTab.slots[slotName]:SetSelItemId(newItem.id)
				build.itemsTab:PopulateSlots()
				build.buildFlag = true
				runCallback("OnFrame")
				return newItem
			end
		end
		error("unique not found: " .. title)
	end

	local function selectGroupWithSkill(name)
		for index, group in ipairs(build.skillsTab.socketGroupList) do
			for _, skill in ipairs(group.displaySkillList or { }) do
				if skill.activeEffect.grantedEffect.name == name then
					build.mainSocketGroup = index
					build.buildFlag = true
					runCallback("OnFrame")
					return group
				end
			end
		end
		error("no socket group with " .. name)
	end

	it("defaults phantasms to their spell projectile", function()
		equipUnique("Soulwrest", "Weapon 1")
		selectGroupWithSkill("Triggered Summon Phantasm")
		local env = build.calcsTab.mainEnv
		assert.is_truthy(env.minion)
		local names = { }
		for _, skill in ipairs(env.minion.activeSkillList) do
			table.insert(names, skill.activeEffect.grantedEffect.name)
		end
		assert.are.equal("Default Attack", names[1])
		assert.are.equal("Physical Projectile", env.minion.mainSkill.activeEffect.grantedEffect.name)
	end)

	it("keeps attack skills for minions that attack", function()
		build.skillsTab:PasteSocketGroup("Raise Zombie 20/0  1")
		runCallback("OnFrame")
		selectGroupWithSkill("Raise Zombie")
		local env = build.calcsTab.mainEnv
		assert.is_truthy(env.minion)
		assert.is_true(env.minion.mainSkill.skillTypes[SkillType.Attack] == true)
	end)
end)
