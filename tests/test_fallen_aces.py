import tests.sublime_stub
import unittest
import tempfile
import os
import json
from unittest.mock import patch, MagicMock

# Import the refactored functions
from fallen_aces import (
    parse_cursor_position,
    get_cursor_position,
    parse_level_info,
    read_world_file_path,
    get_level_info,
    resolve_hover_hint,
    resolve_completions,
    get_function_definitions,
    get_shortcuts,
    format_hint_html,
    _METADATA_CACHE,
    _PROJECT_STRUCTURE_CACHE
)

# ---------------------------------------------------------------------------
# Mocks
# ---------------------------------------------------------------------------

class FakeRegion:
    def __init__(self, begin, end):
        self._begin = begin
        self._end = end
    def begin(self):
        return self._begin
    def end(self):
        return self._end

class FakeView:
    def __init__(self, line="", cursor_point=0, settings=None):
        self._line = line
        self._cursor_point = cursor_point
        self._settings = settings or {"fallen_aces_plugin_debug_enabled": False}
    def settings(self):
        return MagicMock(get=lambda k, d: self._settings.get(k, d))
    def line(self, point):
        return FakeRegion(0, len(self._line))
    def substr(self, region_or_point):
        if isinstance(region_or_point, FakeRegion):
            return self._line[region_or_point.begin():region_or_point.end()]
        return self._line[region_or_point]
    def word(self, point):
        # Simple word extractor for testing
        start = self._line.rfind(" ", 0, point) + 1
        end = self._line.find(" ", point)
        if end == -1: end = len(self._line)
        if "(" in self._line[start:end]: end = self._line.find("(", start)
        return FakeRegion(start, end)
    def window(self):
        return None
    def match_selector(self, point, selector):
        return True
    def extract_completions(self, prefix):
        return ["myVar", "anotherVar"]

# ---------------------------------------------------------------------------
# Metadata Mock Data
# ---------------------------------------------------------------------------

MOCK_METADATA = {
    "functions": [
        {
            "name": "SetState",
            "variants": [
                {
                    "args": ["entityTag", "stateName"],
                    "description": "Sets state.",
                    "usage": "SetState(\"tag\", \"&state\");"
                }
            ]
        },
        {
            "name": "Overloaded",
            "variants": [
                {"args": ["arg1"], "description": "One arg"},
                {"args": ["arg1", "arg2"], "description": "Two args"}
            ]
        }
    ],
    "shortcuts": [
        {"trigger": "ife", "contents": "If(Equal(${1}, ${2}))", "annotation": "If Equals"}
    ]
}

# ---------------------------------------------------------------------------
# Cursor Tests
# ---------------------------------------------------------------------------

class TestCursor(unittest.TestCase):
    def test_parse_cursor_position(self):
        cases = [
            ("SetState(entityTag, stateName);", 4, "SetState", "SetState[2]", None),
            ("SetState(entityTag, stateName);", 12, "SetState", "SetState[2]", 0),
            ("SetState(entityTag, stateName);", 22, "SetState", "SetState[2]", 1),
            ("EndLevel();", 4, "EndLevel", "EndLevel[0]", None),
            ("// comment", 5, None, None, None),
        ]
        for line, offset, name, fid, arg in cases:
            res = parse_cursor_position(line, offset)
            if name is None:
                self.assertIsNone(res)
            else:
                self.assertEqual(res["function_name"], name)
                self.assertEqual(res["function_id"], fid)
                self.assertEqual(res["arg_index"], arg)

    def test_get_cursor_position(self):
        view = FakeView("SetState(tag, state);", cursor_point=10)
        res = get_cursor_position(view, 10)
        self.assertEqual(res["arg_index"], 0)

# ---------------------------------------------------------------------------
# Metadata Tests
# ---------------------------------------------------------------------------

class TestMetadata(unittest.TestCase):
    @patch("fallen_aces.load_plugin_resource")
    def test_get_function_definitions(self, mock_load):
        # Clear cache for clean test
        import fallen_aces
        fallen_aces._METADATA_CACHE = None
        
        mock_load.return_value = json.dumps(MOCK_METADATA)
        
        defs = get_function_definitions()
        self.assertIn("SetState[2]", defs)
        self.assertIn("Overloaded[1]", defs)
        self.assertIn("Overloaded[2]", defs)
        self.assertEqual(defs["SetState[2]"]["name"], "SetState")
        self.assertEqual(defs["SetState[2]"]["args"], ["entityTag", "stateName"])
        self.assertEqual(defs["SetState[2]"]["description"], "Sets state.")

    @patch("fallen_aces.load_plugin_resource")
    def test_get_shortcuts(self, mock_load):
        import fallen_aces
        fallen_aces._METADATA_CACHE = None
        mock_load.return_value = json.dumps(MOCK_METADATA)
        
        shortcuts = get_shortcuts()
        self.assertEqual(len(shortcuts), 1)
        self.assertEqual(shortcuts[0]["trigger"], "ife")

    def test_format_hint_html(self):
        definition = {
            "name": "Test",
            "args": ["a1", "a2"],
            "description": "Desc line\nNext line",
            "usage": "Test(1, 2);"
        }
        html_out = format_hint_html(definition)
        self.assertIn("<b>Test(a1, a2)</b>", html_out)
        self.assertIn("Desc line<br>Next line", html_out)
        self.assertIn("How to use", html_out)
        self.assertIn("background-color:#272822", html_out)
        self.assertIn("Test(1,&nbsp;2);", html_out)

    @patch("fallen_aces.load_plugin_resource")
    def test_get_metadata_missing_file(self, mock_load):
        import fallen_aces
        fallen_aces._METADATA_CACHE = None
        mock_load.return_value = None
        
        defs = get_function_definitions()
        self.assertEqual(defs, {})
        
        shortcuts = get_shortcuts()
        self.assertEqual(shortcuts, [])

# ---------------------------------------------------------------------------
# Level Info Tests
# ---------------------------------------------------------------------------

class TestLevelInfo(unittest.TestCase):
    def test_parse_level_info(self):
        raw = 'Event { name="e1" number=1 } Tag { name="t1" number=10 } Thing { definition_id=517 tag=10 }'
        res = parse_level_info(raw)
        self.assertEqual(res["events"][1], "e1 - 1")
        self.assertEqual(res["tags"][10], "t1 - 10")
        self.assertIn(10, res["things"][517])

    def test_read_world_file_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            chapter_info = os.path.join(tmp, "chapterInfo.txt")
            world_file = os.path.join(tmp, "level.world")
            with open(chapter_info, "w") as f:
                f.write('world_file_name = "level.world"')
            with open(world_file, "w") as f:
                f.write("data")
            
            self.assertEqual(read_world_file_path(chapter_info), world_file)

# ---------------------------------------------------------------------------
# Listener Logic Tests
# ---------------------------------------------------------------------------

class TestListenerLogic(unittest.TestCase):
    def setUp(self):
        self.defs = {
            "Test[1]": {
                "name": "Test",
                "args": ["eventNumber"],
                "description": "Desc",
                "usage": "Usage"
            },
            "Hardcoded[1]": {
                "name": "Hardcoded",
                "args": ["logLevel"]
            },
            "Tagged[1]": {
                "name": "Tagged",
                "args": ["myTag"]
            }
        }
        self.info = {
            "events": {1: "e1 - 1"},
            "tags": {10: "t1 - 10"},
            "things": {517: [10]}
        }

    def test_resolve_hover_hint(self):
        # Function name hover
        cursor = {"function_id": "Test[1]", "function_name": "Test", "arg_index": None}
        hint = resolve_hover_hint("Test", cursor, self.defs, self.info)
        self.assertIn("<b>Test(eventNumber)</b>", hint)
        
        # Event number hover
        cursor["arg_index"] = 0
        self.assertEqual(resolve_hover_hint("1", cursor, self.defs, self.info), "e1 - 1")

    def test_resolve_hover_hint_hardcoded(self):
        cursor = {"function_id": "Hardcoded[1]", "function_name": "Hardcoded", "arg_index": 0}
        self.assertEqual(resolve_hover_hint("0", cursor, self.defs, self.info), "Info")

    def test_resolve_hover_hint_tag(self):
        cursor = {"function_id": "Tagged[1]", "function_name": "Tagged", "arg_index": 0}
        self.assertEqual(resolve_hover_hint("10", cursor, self.defs, self.info), "t1 - 10")

    def test_resolve_completions_args(self):
        cursor = {"function_id": "Test[1]", "arg_index": 0}
        buffer_words = ["myVar"]
        shortcuts = []
        res = resolve_completions(cursor, buffer_words, self.defs, shortcuts, self.info, {})
        self.assertIsNotNone(res)
        self.assertIn(("e1 - 1", "1"), res[0])
        # Check inhibition flags for specialized completions
        self.assertEqual(res[1], tests.sublime_stub.sublime_stub.INHIBIT_WORD_COMPLETIONS | tests.sublime_stub.sublime_stub.INHIBIT_EXPLICIT_COMPLETIONS)

    def test_resolve_completions_general(self):
        cursor = {"function_id": "Unknown[1]", "arg_index": None}
        buffer_words = ["myVar", "anotherVar"]
        shortcuts = [{"trigger": "ife", "contents": "If...", "annotation": "snippet"}]
        
        # Add an overloaded function to defs
        defs = self.defs.copy()
        defs["Over[1]"] = {"name": "Over", "args": ["a1"]}
        defs["Over[2]"] = {"name": "Over", "args": ["a1", "a2"]}

        res = resolve_completions(cursor, buffer_words, defs, shortcuts, self.info, {})
        
        # Check function snippets (including signatures in triggers)
        self.assertTrue(any(c[0] == "Test(eventNumber)\tfn" for c in res[0]))
        self.assertTrue(any(c[0] == "Over(a1)\tfn" for c in res[0]))
        self.assertTrue(any(c[0] == "Over(a1, a2)\tfn" for c in res[0]))
        # Check shortcut
        self.assertTrue(any(c[0] == "ife\tsnippet" for c in res[0]))
        # Check buffer variables
        self.assertTrue(any(c[0] == "myVar\tvar" for c in res[0]))
        self.assertTrue(any(c[0] == "anotherVar\tvar" for c in res[0]))

    def test_parse_cursor_position_nested(self):
        line = "If(Equal(name, value))"
        
        # 1. Cursor on "If"
        res = parse_cursor_position(line, 1)
        self.assertEqual(res["function_name"], "If")
        self.assertEqual(res["function_id"], "If[1]") # Should be If[1], not If[2]
        self.assertIsNone(res["arg_index"])

        # 2. Cursor on "Equal"
        res = parse_cursor_position(line, 4)
        self.assertEqual(res["function_name"], "Equal")
        self.assertEqual(res["function_id"], "Equal[2]")
        self.assertIsNone(res["arg_index"])

        # 3. Cursor on "name" (first arg of Equal)
        res = parse_cursor_position(line, 10)
        self.assertEqual(res["function_name"], "Equal")
        self.assertEqual(res["function_id"], "Equal[2]")
        self.assertEqual(res["arg_index"], 0)

        # 4. Cursor on "value" (second arg of Equal)
        res = parse_cursor_position(line, 16)
        self.assertEqual(res["function_name"], "Equal")
        self.assertEqual(res["function_id"], "Equal[2]")
        self.assertEqual(res["arg_index"], 1)

    def test_resolve_completions_structural_logic(self):
        # Setup mock metadata with tags
        defs = {
            "If[1]": {
                "name": "If",
                "args": ["condition"],
                "tags": ["control"]
            },
            "Equal[2]": {
                "name": "Equal",
                "args": ["name", "value"],
                "tags": ["predicate"]
            },
            "SetState[2]": {
                "name": "SetState",
                "args": ["tag", "state"]
            },
            "IsBroken[1]": {
                "name": "IsBroken",
                "args": ["entityTag"],
                "tags": ["predicate"]
            }
        }
        
        cursor = {"function_id": "Unknown", "arg_index": None}
        res = resolve_completions(cursor, [], defs, [], None, {})
        completions = {c[0]: c[1] for c in res[0]}

        # 1. Control flow (If) should have a block and NO semicolon
        self.assertIn("If(condition)\tfn", completions)
        self.assertTrue(completions["If(condition)\tfn"].startswith("If("))
        self.assertTrue("{" in completions["If(condition)\tfn"], "Control function should complete with a block")
        self.assertFalse(completions["If(condition)\tfn"].endswith(";"), "Control function should not have a semicolon")

        # 2. Predicate (Equal) should have NO semicolon
        self.assertIn("Equal(name, value)\tfn", completions)
        self.assertFalse(completions["Equal(name, value)\tfn"].endswith(";"), "Predicate function should not have a semicolon")

        # 3. Standard function (SetState) SHOULD have a semicolon
        self.assertIn("SetState(tag, state)\tfn", completions)
        self.assertTrue(completions["SetState(tag, state)\tfn"].endswith(";"), "Standard function should have a semicolon")

        # 4. Predicate-like function (IsBroken) should also have NO semicolon
        self.assertIn("IsBroken(entityTag)\tfn", completions)
        self.assertFalse(completions["IsBroken(entityTag)\tfn"].endswith(";"), "IsBroken should be a predicate and have no semicolon")

    def test_resolve_completions_deduplication(self):
        # Test that buffer words don't duplicate function names
        cursor = {"function_id": "Unknown", "arg_index": None}
        buffer_words = ["Test"] # "Test" is already a function
        shortcuts = []
        
        res = resolve_completions(cursor, buffer_words, self.defs, shortcuts, self.info, {})
        
        test_entries = [c for c in res[0] if c[1] == "Test" or c[1].startswith("Test(")]
        # Should only have the function entry "Test(eventNumber)", not "Test" as var
        self.assertEqual(len(test_entries), 1)
        self.assertIn("\tfn", test_entries[0][0])

    def test_resolve_completions_local_functions(self):
        cursor = {"function_id": "Unknown", "arg_index": None}
        buffer_words = []
        # Local functions discovered by the listener with arguments
        local_functions = {"MyLocalFunction": ["arg1", "arg2"]}

        # Test: Should appear with arguments in trigger and placeholders in snippet
        res = resolve_completions(cursor, buffer_words, {}, [], None, local_functions)
        completions = {c[0]: c[1] for c in res[0]}
        
        # 1. Trigger should show arguments
        self.assertIn("MyLocalFunction(arg1, arg2)\tfn", completions)
        # 2. Snippet should use placeholders
        self.assertEqual(completions["MyLocalFunction(arg1, arg2)\tfn"], "MyLocalFunction(${1:arg1}, ${2:arg2});")

    def test_resolve_completions_case_insensitive(self):
        cursor = {"function_id": "Unknown", "arg_index": None}
        # Predefined function
        defs = {"SetState[2]": {"name": "SetState", "args": ["a", "b"]}}
        # Buffer word matches predefined function but with different case
        buffer_words = ["setstate"]
        
        res = resolve_completions(cursor, buffer_words, defs, [], None, {})
        completions = [c[0] for c in res[0]]
        
        # Should only have the function entry, not the lowercase "var" entry
        self.assertTrue(any(c.startswith("SetState(") for c in completions))
        self.assertFalse(any(c == "setstate\tvar" for c in completions))

    def test_resolve_completions_no_level_info(self):
        cursor = {"function_id": "Test[1]", "arg_index": 0}
        buffer_words = []
        shortcuts = []
        # level_info is None
        res = resolve_completions(cursor, buffer_words, self.defs, shortcuts, None, {})
        # Should not crash, and since it's an arg completion but no info, it might proceed to general
        self.assertTrue(any(c[0].startswith("Test(eventNumber)\tfn") for c in res[0]))

if __name__ == "__main__":
    unittest.main()
