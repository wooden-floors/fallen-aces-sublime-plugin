import sys
import os
# Add the package root to sys.path so we can import 'logic' and 'utils' directly in tests
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tests.sublime_stub
import unittest
import tempfile
import json
from unittest.mock import patch, MagicMock

# Import the logic modules directly for cache management
import fa_core.definition_provider as definitions_logic
import fa_core.world_data_provider as world_data_logic
from fa_utils import logger
from fa_utils.formatter import format_hint_html

# Import the glue functions from the main plugin file
from fallen_aces import (
    get_cursor_position,
    get_world_data,
    create_hover_context,
    create_completion_context
)
from fa_core.resolver import resolve_hover_hint, resolve_completions
from fa_parser.world_parser import parse_world_file, Event, Tag, WorldData
from fa_parser.chapter_info_parser import get_world_file_path

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
        # Support any object with begin() and end() (like FakeRegion or parser's RegionStub)
        if hasattr(region_or_point, "begin") and hasattr(region_or_point, "end"):
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
    def size(self):
        return len(self._line)

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
    def test_get_cursor_position(self):
        view = FakeView("SetState(tag, state);", cursor_point=10)
        res = get_cursor_position(view, 10)
        self.assertEqual(res["arg_index"], 0)

# ---------------------------------------------------------------------------
# Definitions Tests
# ---------------------------------------------------------------------------

class TestDefinitions(unittest.TestCase):
    @patch("fallen_aces.load_plugin_resource")
    def test_get_definitions_lazy_loading(self, mock_load):
        # Reset provider state
        definitions_logic.provider.clear_cache()
        
        # Setup mock data for the loader
        mock_load.return_value = json.dumps(MOCK_METADATA)
        
        # Calling getter should trigger lazy load via provider
        defs = definitions_logic.provider.get_function_definitions()
        self.assertIn("SetState[2]", defs)
        self.assertEqual(mock_load.call_count, 1)
        
        # Subsequent call should NOT trigger another load
        definitions_logic.provider.get_function_definitions()
        self.assertEqual(mock_load.call_count, 1)

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

# ---------------------------------------------------------------------------
# Level Info Tests
# ---------------------------------------------------------------------------

class TestLevelInfo(unittest.TestCase):
    def test_read_world_file_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            chapter_info = os.path.join(tmp, "chapterInfo.txt")
            world_file = os.path.join(tmp, "world.txt")
            with open(chapter_info, "w") as f:
                f.write('world_file_name = "world.txt"')
            with open(world_file, "w") as f:
                f.write("data")
            
            self.assertEqual(get_world_file_path(chapter_info), world_file)

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
        self.info = WorldData(
            events={1: Event("e1", 1)},
            tags={10: Tag("t1", 10)},
            things={517: [10]}
        )

    def mock_context(self, cursor):
        """Creates a mock RequestContext for listener tests."""
        mock_ctx = MagicMock()
        mock_ctx.cursor = cursor
        mock_ctx.world_data = self.info
        mock_ctx.definitions = self.defs
        mock_ctx.shortcuts = []
        mock_ctx.local_functions = {}
        mock_ctx.buffer_words = []
        mock_ctx.hardcoded_suggestions = {
            "logLevel": {"0": "Info"}
        }
        mock_ctx.variable_to_definition_id = {
            "lightStateTag": {"517": "LightState"}
        }
        return mock_ctx

    def test_resolve_hover_hint(self):
        # Function name hover
        cursor = {"function_id": "Test[1]", "function_name": "Test", "arg_index": None}
        ctx = self.mock_context(cursor)
        hint = resolve_hover_hint("Test", ctx)
        self.assertIn("<b>Test(eventNumber)</b>", hint)
        
        # Event number hover
        cursor["arg_index"] = 0
        self.assertEqual(resolve_hover_hint("1", ctx), "e1 - 1")

    def test_resolve_hover_hint_hardcoded(self):
        cursor = {"function_id": "Hardcoded[1]", "function_name": "Hardcoded", "arg_index": 0}
        ctx = self.mock_context(cursor)
        self.assertEqual(resolve_hover_hint("0", ctx), "Info")

    def test_resolve_hover_hint_tag(self):
        cursor = {"function_id": "Tagged[1]", "function_name": "Tagged", "arg_index": 0}
        ctx = self.mock_context(cursor)
        self.assertEqual(resolve_hover_hint("10", ctx), "t1 - 10")

    def test_resolve_completions_args(self):
        cursor = {"function_id": "Test[1]", "arg_index": 0}
        ctx = self.mock_context(cursor)
        ctx.buffer_words = ["myVar"]
        res = resolve_completions(ctx)
        self.assertIsNotNone(res)
        self.assertIn(("e1 - 1", "1"), res)

    def test_resolve_completions_general(self):
        cursor = {"function_id": "Unknown[1]", "arg_index": None}
        ctx = self.mock_context(cursor)
        ctx.buffer_words = ["myVar", "anotherVar"]
        ctx.shortcuts = [{"trigger": "ife", "contents": "If...", "annotation": "snippet"}]
        
        # Add an overloaded function to defs
        ctx.definitions["Over[1]"] = {"name": "Over", "args": ["a1"]}
        ctx.definitions["Over[2]"] = {"name": "Over", "args": ["a1", "a2"]}

        res = resolve_completions(ctx)
        
        # Check function snippets
        self.assertTrue(any(c[0] == "Test(eventNumber)\tfn" for c in res))
        self.assertTrue(any(c[0] == "Over(a1)\tfn" for c in res))
        self.assertTrue(any(c[0] == "Over(a1, a2)\tfn" for c in res))
        # Check buffer variables
        self.assertTrue(any(c[0] == "myVar\tvar" for c in res))

    def test_resolve_completions_structural_logic(self):
        ctx = self.mock_context(None)
        ctx.definitions = {
            "If[1]": {"name": "If", "args": ["condition"], "tags": ["control"]},
            "Equal[2]": {"name": "Equal", "args": ["name", "value"], "tags": ["predicate"]},
            "SetState[2]": {"name": "SetState", "args": ["tag", "state"]}
        }
        
        res = resolve_completions(ctx)
        completions = {c[0]: c[1] for c in res}

        # 1. Control flow (If) should have a block and NO semicolon
        self.assertTrue("{" in completions["If(condition)\tfn"])
        self.assertFalse(completions["If(condition)\tfn"].endswith(";"))

        # 2. Standard function SHOULD have a semicolon
        self.assertTrue(completions["SetState(tag, state)\tfn"].endswith(";"))

    def test_resolve_completions_deduplication(self):
        ctx = self.mock_context(None)
        ctx.buffer_words = ["Test"]
        
        res = resolve_completions(ctx)
        
        # Each entry in res is a tuple (trigger, content)
        test_entries = [c for c in res if c[1] == "Test" or (isinstance(c[1], str) and c[1].startswith("Test("))]
        self.assertEqual(len(test_entries), 1)
        self.assertIn("\tfn", test_entries[0][0])

    def test_resolve_completions_local_functions(self):
        ctx = self.mock_context(None)
        ctx.definitions = {}
        ctx.local_functions = {"MyLocalFunction": ["arg1", "arg2"]}

        res = resolve_completions(ctx)
        completions = {c[0]: c[1] for c in res}
        
        self.assertIn("MyLocalFunction(arg1, arg2)\tfn", completions)
        self.assertEqual(completions["MyLocalFunction(arg1, arg2)\tfn"], "MyLocalFunction(${1:arg1}, ${2:arg2});")

    def test_resolve_completions_case_insensitive(self):
        ctx = self.mock_context(None)
        ctx.definitions = {"SetState[2]": {"name": "SetState", "args": ["a", "b"]}}
        ctx.buffer_words = ["setstate"]
        
        res = resolve_completions(ctx)
        # c is a tuple (trigger, content)
        triggers = [c[0] for c in res]
        
        self.assertTrue(any(t.startswith("SetState(") for t in triggers))
        self.assertFalse(any(t == "setstate\tvar" for t in triggers))

    def test_resolve_completions_no_world_data(self):
        ctx = self.mock_context({"function_id": "Test[1]", "arg_index": 0})
        ctx.world_data = None
        res = resolve_completions(ctx)
        # Should proceed to general suggestions
        self.assertTrue(any(c[0].startswith("Test(eventNumber)\tfn") for c in res))

class TestSyntaxApplication(unittest.TestCase):
    def setUp(self):
        from fallen_aces import FallenAcesScriptEventListener
        self.listener = FallenAcesScriptEventListener()

    def test_syntax_applied_when_enabled_and_in_scripts(self):
        view = MagicMock()
        view.settings().get.side_effect = lambda k, d=None: {
            "fallen_aces_auto_syntax_enabled": True,
            "syntax": "Other"
        }.get(k, d)
        view.file_name.return_value = os.path.join("some", "scripts", "test.txt")
        
        self.listener._check_and_apply_syntax(view)
        
        view.set_syntax_file.assert_called_once()
        self.assertIn("fallen-aces.sublime-syntax", view.set_syntax_file.call_args[0][0])

    def test_syntax_not_applied_when_disabled(self):
        view = MagicMock()
        view.settings().get.return_value = False
        view.file_name.return_value = os.path.join("some", "scripts", "test.txt")
        
        self.listener._check_and_apply_syntax(view)
        
        view.set_syntax_file.assert_not_called()

    def test_syntax_not_applied_outside_scripts(self):
        view = MagicMock()
        view.settings().get.return_value = True
        view.file_name.return_value = os.path.join("some", "other", "test.txt")
        
        self.listener._check_and_apply_syntax(view)
        
        view.set_syntax_file.assert_not_called()

if __name__ == "__main__":
    unittest.main()
