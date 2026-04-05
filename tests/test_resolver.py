# tests/test_resolver.py
import sys
import os
import unittest

# Add the package root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fa_core.resolver import resolve_hover_hint, resolve_completions, HoverContext, CompletionContext
from fa_parser.world_parser import WorldData, Event, Tag

class TestResolver(unittest.TestCase):
    def setUp(self):
        # Sample data for tests
        self.defs = {
            "SetState[2]": {
                "name": "SetState",
                "args": ["entityTag", "stateName"],
                "description": "Sets state."
            },
            "TriggerEvent[1]": {
                "name": "TriggerEvent",
                "args": ["eventNumber"]
            },
            "Log[2]": {
                "name": "Log",
                "args": ["msg", "logLevel"]
            },
            "CreateDisturbance[3]": {
                "name": "CreateDisturbance",
                "args": ["disturbanceTypeName", "pos", "target"]
            }
        }
        self.world_data = WorldData(
            events={101: Event("MyEvent", 101)},
            tags={50: Tag("MyTag", 50)},
            things={517: [50]} # 517 is lightStateTag
        )
        self.hardcoded_suggestions = {
            "logLevel": {
                "0": "Info",
                "1": "Warning"
            },
            "disturbanceTypeName": {
                "type": "string",
                "options": {
                    "SomethingOn": "SomethingOn",
                    "SomethingOff": "SomethingOff"
                }
            }
        }
        self.variable_to_definition_id = {
            "entityTag": {"517": "LightState"},
            "lightStateTag": {"517": "LightState"}
        }

    def create_hover_context(self, cursor=None):
        """Helper to create a HoverContext for testing."""
        return HoverContext(
            cursor=cursor,
            world_data=self.world_data,
            definitions=self.defs,
            hardcoded_suggestions=self.hardcoded_suggestions
        )

    def create_completion_context(self, cursor=None, buffer_words=None, buffer_strings=None, local_functions=None, shortcuts=None):
        """Helper to create a CompletionContext for testing."""
        return CompletionContext(
            cursor=cursor,
            world_data=self.world_data,
            definitions=self.defs,
            shortcuts=shortcuts or [],
            local_functions=local_functions or {},
            buffer_words=buffer_words or [],
            buffer_strings=buffer_strings or [],
            variable_to_definition_id=self.variable_to_definition_id,
            hardcoded_suggestions=self.hardcoded_suggestions
        )

    def test_string_literal_completions(self):
        # 1. Cursor inside a string
        cursor = {"function_id": "SetWorldVariable[2]", "function_name": "SetWorldVariable", "arg_index": 0, "is_string": True}
        buffer_strings = ["my_var_1", "my_var_2"]
        ctx = self.create_completion_context(cursor=cursor, buffer_strings=buffer_strings)

        completions = resolve_completions(ctx)
        
        # Should only contain string literals from the buffer
        self.assertEqual(len(completions), 2)
        self.assertEqual(completions[0][1], "my_var_1")
        self.assertEqual(completions[1][1], "my_var_2")
        self.assertIn("\tstr", completions[0][0])

    # --- resolve_hover_hint Tests ---

    def test_hover_on_function_name(self):
        cursor = {"function_name": "SetState", "function_id": "SetState[2]", "arg_index": None}
        ctx = self.create_hover_context(cursor=cursor)
        hint = resolve_hover_hint("SetState", ctx)
        self.assertIsNotNone(hint)
        self.assertIn("<b>SetState(entityTag, stateName)</b>", hint)

    def test_hover_on_event_number(self):
        cursor = {"function_name": "TriggerEvent", "function_id": "TriggerEvent[1]", "arg_index": 0}
        ctx = self.create_hover_context(cursor=cursor)
        hint = resolve_hover_hint("101", ctx)
        self.assertEqual(hint, "MyEvent - 101")

    def test_hover_on_tag(self):
        cursor = {"function_name": "SetState", "function_id": "SetState[2]", "arg_index": 0}
        ctx = self.create_hover_context(cursor=cursor)
        hint = resolve_hover_hint("50", ctx)
        self.assertEqual(hint, "MyTag - 50")

    def test_hover_on_hardcoded_enum(self):
        cursor = {"function_name": "Log", "function_id": "Log[2]", "arg_index": 1}
        ctx = self.create_hover_context(cursor=cursor)
        hint = resolve_hover_hint("0", ctx)
        self.assertEqual(hint, "Info")

    def test_hover_on_function_name_fallback(self):
        # Case: parser says [1] (empty call), but only [0] exists
        self.defs["EndLevel[0]"] = {"name": "EndLevel", "args": []}
        cursor = {"function_name": "EndLevel", "function_id": "EndLevel[1]", "arg_index": 0}
        ctx = self.create_hover_context(cursor=cursor)
        hint = resolve_hover_hint("EndLevel", ctx)
        self.assertIsNotNone(hint)
        self.assertIn("<b>EndLevel()</b>", hint)

    def test_hover_no_hint(self):
        cursor = {"function_name": "Unknown", "function_id": "Unknown[0]", "arg_index": None}
        ctx = self.create_hover_context(cursor=cursor)
        self.assertIsNone(resolve_hover_hint("Unknown", ctx))

    # --- resolve_completions Tests ---

    def test_completions_for_event_number(self):
        cursor = {"function_id": "TriggerEvent[1]", "arg_index": 0}
        ctx = self.create_completion_context(cursor=cursor)
        res = resolve_completions(ctx)
        self.assertIn(("MyEvent - 101", "101"), res)

    def test_completions_for_tags_by_name(self):
        cursor = {"function_id": "SetState[2]", "arg_index": 0}
        ctx = self.create_completion_context(cursor=cursor)
        res = resolve_completions(ctx)
        self.assertIn(("MyTag - 50", "50"), res)

    def test_completions_for_hardcoded_suggestions(self):
        cursor = {"function_id": "Log[2]", "arg_index": 1}
        ctx = self.create_completion_context(cursor=cursor)
        res = resolve_completions(ctx)
        self.assertIn(("Info", "0"), res)
        self.assertIn(("Warning", "1"), res)

    def test_completions_for_event_number_fallback(self):
        # Case: parser says [0] (not possible with current parser, but testing resolver robustness), 
        # but only [1] exists. Or parser says [2] but only [1] exists.
        cursor = {"function_name": "TriggerEvent", "function_id": "TriggerEvent[2]", "arg_index": 0}
        ctx = self.create_completion_context(cursor=cursor)
        res = resolve_completions(ctx)
        self.assertIn(("MyEvent - 101", "101"), res)

    def test_general_completions(self):
        buffer_words = ["myVar"]
        shortcuts = [{"trigger": "ife", "contents": "If...", "annotation": "snip"}]
        local_funcs = {"MyFunc": ["a"]}
        ctx = self.create_completion_context(buffer_words=buffer_words, shortcuts=shortcuts, local_functions=local_funcs)
        
        res = resolve_completions(ctx)
        triggers = [c[0] for c in res]
        
        self.assertTrue(any(t.startswith("SetState(") for t in triggers))
        self.assertIn("ife\tsnip", triggers)
        self.assertIn("myVar\tvar", triggers)
        self.assertTrue(any(t.startswith("MyFunc(") for t in triggers))

    def test_completions_for_string_hardcoded_suggestions(self):
        # 1. Outside string - should have quotes
        cursor = {"function_id": "CreateDisturbance[3]", "arg_index": 0, "is_string": False}
        ctx = self.create_completion_context(cursor=cursor)
        res = resolve_completions(ctx)
        self.assertIn(("SomethingOn", "\"SomethingOn\""), res)

        # 2. Inside string - should NOT have extra quotes
        cursor = {"function_id": "CreateDisturbance[3]", "arg_index": 0, "is_string": True}
        ctx = self.create_completion_context(cursor=cursor)
        res = resolve_completions(ctx)
        self.assertIn(("SomethingOn", "SomethingOn"), res)

    def test_hover_on_string_hardcoded_enum(self):
        cursor = {"function_name": "CreateDisturbance", "function_id": "CreateDisturbance[3]", "arg_index": 0}
        ctx = self.create_hover_context(cursor=cursor)
        
        # Should not show hints for strings (only digits)
        self.assertIsNone(resolve_hover_hint("SomethingOn", ctx))
        self.assertIsNone(resolve_hover_hint("\"SomethingOn\"", ctx))

    def test_completions_deduplication(self):
        buffer_words = ["SetState", "uniqueVar"]
        ctx = self.create_completion_context(buffer_words=buffer_words)
        
        res = resolve_completions(ctx)
        triggers = [c[0] for c in res]
        self.assertTrue(any(t.startswith("SetState(") for t in triggers))
        self.assertNotIn("SetState\tvar", triggers)
        self.assertIn("uniqueVar\tvar", triggers)

if __name__ == "__main__":
    unittest.main()
