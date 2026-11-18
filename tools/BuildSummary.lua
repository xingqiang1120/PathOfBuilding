-- Path of Building
--
-- Build summary (headless): loads build XML files and writes a structured JSON summary per build
-- (character, skills with per-group DPS, equipped items with tags, passives, key stats, config
-- assumptions, modifier coverage). Used by tools/library.py and for AI analysis.
--
--   python tools/runlua.py tools/BuildSummary.lua <build.xml> [out.json]
--   python tools/runlua.py tools/BuildSummary.lua --out-dir <dir> <a.xml> <b.xml> ...
--
-- In --out-dir mode PoB is loaded once; each <name>.xml produces <dir>/<name>.json. A build that
-- fails to load produces { "error": "..." } instead of stopping the batch.

local files, outDir, singleOut = { }, nil, nil
if SCRIPT_ARGS[1] == "--out-dir" then
	outDir = SCRIPT_ARGS[2]
	for i = 3, #SCRIPT_ARGS do table.insert(files, SCRIPT_ARGS[i]) end
else
	files[1], singleOut = SCRIPT_ARGS[1], SCRIPT_ARGS[2]
end
assert(files[1], "usage: BuildSummary.lua <build.xml> [out.json] | --out-dir <dir> <a.xml> ...")

dofile("HeadlessWrapper.lua")
local dkjson = require("dkjson")

local function readFile(path)
	local f = assert(io.open(path, "rb"))
	local text = f:read("*a")
	f:close()
	return text
end

local function writeFile(path, text)
	local f = assert(io.open(path, "wb"))
	f:write(text)
	f:close()
end

local S = dofile(SCRIPT_DIR .. "/lib/summary.lua")
local summarize = S.summarize

for _, path in ipairs(files) do
	local buildName = path:match("([^/\\]+)%.xml$") or "build"
	local ok, result = pcall(summarize, readFile(path), buildName)
	local summary = ok and result or { name = buildName, error = tostring(result) }
	local json = dkjson.encode(summary, { indent = true })
	if outDir then
		writeFile(outDir .. "/" .. buildName .. ".json", json)
		print((ok and "ok    " or "error ") .. buildName .. (ok and "" or (": " .. tostring(result))))
	elseif singleOut then
		writeFile(singleOut, json)
		print("written: " .. singleOut)
	else
		print(json)
	end
end
