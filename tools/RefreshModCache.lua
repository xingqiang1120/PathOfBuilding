-- Path of Building
--
-- Re-parse the entries of src/Data/ModCache.lua whose text contains a filter, with the current
-- ModParser, and rewrite only those lines in place. Use after adding a parser rule: the cache is
-- pre-generated, so a new rule has no effect on cached lines (passive tree, uniques) until refreshed.
-- Regenerating the whole cache would touch thousands of unrelated lines.
--
--   python tools/runlua.py tools/RefreshModCache.lua "mercenary"     (case-insensitive substring)

local filter = assert(SCRIPT_ARGS[1], "usage: RefreshModCache.lua <text filter>"):lower()
dofile("HeadlessWrapper.lua")

local path = "Data/ModCache.lua"
local f = assert(io.open(path, "rb"))
local text = f:read("*a")
f:close()
local crlf = text:find("\r\n", 1, true) ~= nil

-- Same entry format as main:SaveModCache
local function entryLine(line, dat)
	local parts = { }
	local out = { write = function(_, ...) for _, s in ipairs({ ... }) do table.insert(parts, s) end end }
	out:write('c["', (line:gsub("\n", "\\n")), '"]={')
	if dat[1] then
		writeLuaTable(out, dat[1])
	else
		out:write("nil")
	end
	if dat[2] then
		out:write(',"', (dat[2]:gsub("\n", "\\n")), '"}')
	else
		out:write(",nil}")
	end
	return table.concat(parts)
end

local changed, checked = 0, 0
local lines = { }
for raw in (text:gsub("\r\n", "\n")):gmatch("([^\n]*)\n") do
	local key = raw:match('^c%["(.-)"%]={')
	if key and key:lower():find(filter, 1, true) then
		checked = checked + 1
		local line = key:gsub("\\n", "\n")
		modLib.parseModCache[line] = nil
		local list, extra = modLib.parseMod(line)
		local new = entryLine(line, { list, extra })
		if new ~= raw then
			changed = changed + 1
			print((list and not extra) and "parsed:   " or "changed:  ", line)
		end
		raw = new
	end
	table.insert(lines, raw)
end
local out = assert(io.open(path, "wb"))
out:write(table.concat(lines, crlf and "\r\n" or "\n"), crlf and "\r\n" or "\n")
out:close()
print(string.format("%d cache entries matched '%s', %d changed", checked, filter, changed))
