# tests/test_resolver.py
import sys
import os
import unittest

# Add the package root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.resolver import resolve_hover_hint, resolve_completions, HoverContext, CompletionContext
from parser.world_parser import WorldData, Event, Tag

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

    def create_completion_context(self, cursor=None, buffer_words=None, local_functions=None, shortcuts=None):
        """Helper to create a CompletionContext for testing."""
        return CompletionContext(
            cursor=cursor,
            world_data=self.world_data,
            definitions=self.defs,
            shortcuts=shortcuts or [],
            local_functions=local_functions or {},
            buffer_words=buffer_words or [],
            variable_to_definition_id=self.variable_to_definition_id,
            hardcoded_suggestions=self.hardcoded_suggestions
        )

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
