-- Path of Building
--
-- Module: Auto Tag Editor
-- Popup for editing the user tags of an item or passive node (opened with Ctrl+T).
--
local t_insert = table.insert
local m_max = math.max

autoTagEditor = { }

local function wrapLabels(labels, maxChars)
	local lines, cur = { }, ""
	for _, label in ipairs(labels) do
		local piece = cur == "" and label or (cur .. ", " .. label)
		if #piece > maxChars and cur ~= "" then
			t_insert(lines, cur .. ",")
			cur = label
		else
			cur = piece
		end
	end
	if cur ~= "" then
		t_insert(lines, cur)
	end
	return lines
end

---Open the editor.
---@param kind "item"|"node"
---@param key any @Storage key (item title or node id)
---@param displayName string
---@param ruleTags table<string, boolean> @Tags derived without user overrides, shown for reference
local function open(kind, key, displayName, ruleTags)
	local controls = { }
	local width = 620
	local y = 20
	local ruleLabels = autoTags.Describe(ruleTags)
	controls.autoLabel = new("LabelControl"):LabelControl({"TOPLEFT",nil,"TOPLEFT"}, {15, y, 0, 16}, "^7Automatic tags:")
	y = y + 18
	local autoLines = #ruleLabels > 0 and wrapLabels(ruleLabels, 80) or { "^8(none)" }
	for i, line in ipairs(autoLines) do
		controls["auto"..i] = new("LabelControl"):LabelControl({"TOPLEFT",nil,"TOPLEFT"}, {25, y, 0, 14}, "^x8888FF"..line)
		y = y + 16
	end
	y = y + 8
	controls.editLabel = new("LabelControl"):LabelControl({"TOPLEFT",nil,"TOPLEFT"}, {15, y, 0, 16}, "^7Your tags (comma separated):")
	y = y + 20
	controls.edit = new("EditControl"):EditControl({"TOPLEFT",nil,"TOPLEFT"}, {15, y, width - 30, 20}, autoTags.FormatEditString(kind, key), nil, "%c", 300)
	y = y + 26
	local help = {
		"^8Name  ^7: add a tag; a new name creates a custom tag",
		"^8Parent/Child  ^7: add a sub-tag, e.g. ^8Minion/My Zombie Build",
		"^8-Name  ^7: remove an automatic tag, e.g. ^8-Life",
	}
	for i, line in ipairs(help) do
		controls["help"..i] = new("LabelControl"):LabelControl({"TOPLEFT",nil,"TOPLEFT"}, {15, y, 0, 14}, line)
		y = y + 16
	end
	local userTags = autoTags.GetUserTags()
	if #userTags > 0 then
		local names = { }
		for _, def in ipairs(userTags) do
			t_insert(names, def.label)
		end
		y = y + 6
		controls.customLabel = new("LabelControl"):LabelControl({"TOPLEFT",nil,"TOPLEFT"}, {15, y, 0, 14}, "^7Your custom tags:")
		y = y + 16
		for i, line in ipairs(wrapLabels(names, 80)) do
			controls["custom"..i] = new("LabelControl"):LabelControl({"TOPLEFT",nil,"TOPLEFT"}, {25, y, 0, 14}, "^xE0C060"..line)
			y = y + 16
		end
	end
	y = y + 14
	controls.save = new("ButtonControl"):ButtonControl(nil, {-50, y, 90, 20}, "Save", function()
		local add, remove = autoTags.ParseEditString(controls.edit.buf)
		autoTags.SetUserEntry(kind, key, add, remove)
		autoTags.SetUserEntryName(kind, key, displayName)
		local ok, errMsg = autoTags.SaveUserFile()
		main:ClosePopup()
		if autoTags.userFilePath and not ok then
			main:OpenMessagePopup("Tags", "Could not save tags: "..tostring(errMsg))
		end
	end)
	controls.cancel = new("ButtonControl"):ButtonControl(nil, {50, y, 90, 20}, "Cancel", function()
		main:ClosePopup()
	end)
	main:OpenPopup(width, y + 34, "Edit Tags: "..displayName, controls, "save", "edit", "cancel")
end

function autoTagEditor.OpenForItem(item)
	if not item then
		return
	end
	local key = autoTags.GetItemKey(item)
	if key then
		open("item", key, key, autoTags.GetItemRuleTags(item))
	end
end

function autoTagEditor.OpenForNode(node)
	if not node or not node.id or node.type == "ClassStart" or node.type == "AscendClassStart" then
		return
	end
	open("node", autoTags.GetNodeKey(node), node.dn or tostring(node.id), autoTags.GetNodeRuleTags(node))
end
