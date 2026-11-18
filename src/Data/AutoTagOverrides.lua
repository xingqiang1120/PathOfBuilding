-- Path of Building
--
-- Auto tag overrides
-- Hand-maintained additions on top of the rule-based tags in Data/AutoTagRules.lua.
-- Use this for deeper / build-specific classification that cannot be derived from modifiers.
--
--   tags   Extra tag definitions. A tag with a "parent" also grants its parent tag, so filtering
--          by the parent still finds items or nodes that only carry the more specific tag.
--   items  Keyed by unique item name (title). add / remove are lists of tag ids.
--   nodes  Keyed by passive node name or numeric node id. add / remove are lists of tag ids.
--
-- Example:
--   tags = {
--     { id = "srs", label = "Summon Raging Spirit", category = "Skill", parent = "minion" },
--   },
--   items = {
--     ["Kalisa's Crescendo"] = { add = { "srs" } },
--   },
--   nodes = {
--     ["Death Attunement"] = { remove = { "spell" } },
--   },

return {
	tags = {
	},
	items = {
	},
	nodes = {
	},
}
