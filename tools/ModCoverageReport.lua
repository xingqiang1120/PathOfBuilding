-- Path of Building
--
-- Modifier coverage report (headless).
--
--   python tools/runlua.py tools/ModCoverageReport.lua [options]
--
-- Options:
--   --out <dir>          Output directory (default: ../reports, i.e. <repo>/reports)
--   --build <file.xml>   Report only what this build uses (equipped items + allocated passives)
--   --previous <file>    Earlier JSON report to compare with (default for the full report:
--                        <out>/coverage.json if it exists, read before it is overwritten)
--   --tree-compare <ver> Previous passive tree version to compare with, e.g. 3_29
--                        (default: the version before the latest one)
--
-- Writes <name>.md (for people) and <name>.json (for tools / AI), where <name> is "coverage" or
-- "build-<build file name>".

local opts = { }
local i = 1
while SCRIPT_ARGS[i] do
	local key = SCRIPT_ARGS[i]:match("^%-%-(.+)$")
	if key then
		opts[key] = SCRIPT_ARGS[i + 1]
		i = i + 2
	else
		i = i + 1
	end
end

dofile("HeadlessWrapper.lua")
local dkjson = require("dkjson")

local outDir = (opts.out or "../reports"):gsub("[/\\]$", "")
-- MakeDir is a no-op in headless mode, so create the directory through the shell
if package.config:sub(1, 1) == "\\" then
	os.execute('if not exist "' .. outDir:gsub("/", "\\") .. '" mkdir "' .. outDir:gsub("/", "\\") .. '"')
else
	os.execute('mkdir -p "' .. outDir .. '"')
end

local function readFile(path)
	local f = io.open(path, "rb")
	if not f then
		return nil
	end
	local text = f:read("*a")
	f:close()
	return text
end

local function writeFile(path, text)
	local f = assert(io.open(path, "wb"))
	f:write(text)
	f:close()
end

local name, entries, reportOpts
if opts.build then
	local xmlText = readFile(opts.build)
	assert(xmlText, "Cannot read build file " .. opts.build)
	local buildName = opts.build:match("([^/\\]+)%.xml$") or "build"
	loadBuildFromXML(xmlText, buildName)
	name = "build-" .. buildName:gsub("[^%w%-_]", "_")
	entries = modCoverage.ScanBuild(build)
	reportOpts = { title = "Modifier coverage: " .. buildName, tree = build.spec.tree }
else
	name = "coverage"
	entries = modCoverage.ScanUniques()
	local tree = main:LoadTree(latestTreeVersion)
	for _, e in ipairs(modCoverage.ScanTree(tree)) do
		table.insert(entries, e)
	end
	local previousTreeVersion = opts["tree-compare"]
	if not previousTreeVersion then
		for idx = #treeVersionList - 1, 1, -1 do
			local ver = treeVersionList[idx]
			if not ver:match("ruthless") and not ver:match("alternate") then
				previousTreeVersion = ver
				break
			end
		end
	end
	reportOpts = { title = "Modifier coverage: all uniques and passive tree", tree = tree, previousTree = previousTreeVersion and main:LoadTree(previousTreeVersion) }
end

local previousPath = opts.previous or (outDir .. "/" .. name .. ".json")
local previousText = readFile(previousPath)
if previousText then
	reportOpts.previous = dkjson.decode(previousText)
end

local report = modCoverage.BuildReport(entries, reportOpts)
local jsonTable = modCoverage.ToJSONTable(report)
writeFile(outDir .. "/" .. name .. ".json", dkjson.encode(jsonTable, { indent = true, keyorder = { "kind", "source", "detail", "nodeId", "line", "status", "impact", "statIds" } }))
writeFile(outDir .. "/" .. name .. ".md", modCoverage.ToMarkdown(report))

for kind, s in pairs(report.summary) do
	print(string.format("%-7s lines=%d unsupported=%d (mapped to stat id: %d) offence=%d defence=%d utility=%d cosmetic=%d",
		kind, s.lines, s.unsupported, s.mapped, s.impact.offence or 0, s.impact.defence or 0, s.impact.utility or 0, s.impact.cosmetic or 0))
end
if report.diff then
	print(string.format("compared with previous report: %d newly unsupported, %d now supported", #report.diff.added, #report.diff.fixed))
end
if report.treeDiff then
	print(string.format("tree %s vs %s: %d new unsupported line texts", report.treeVersion, report.treeDiff.previousTreeVersion, #report.treeDiff.newUnsupported))
end
print("written: " .. outDir .. "/" .. name .. ".md / .json")
