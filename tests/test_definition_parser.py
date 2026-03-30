# tests/test_definition_parser.py
import sys
import os
import unittest
import json

# Add the package root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parser.definition_parser import parse_definitions

class TestDefinitionParser(unittest.TestCase):
    def test_parse_definitions_exhaustive(self):
        """
        Verifies every single field in the JSON structure is correctly 
        mapped to the internal dictionary.
        """
        data = {
            "functions": [
                {
                    "name": "SetState",
                    "tags": ["tag1", "tag2"],
                    "variants": [
                        {
                            "args": ["arg1", "arg2"],
                            "description": "Variant description",
                            "usage": "Variant usage"
                        }
                    ]
                }
            ],
            "shortcuts": [
                {
                    "trigger": "ife",
                    "contents": "If(Equal(${1}, ${2}))",
                    "annotation": "If Equals"
                }
            ]
        }
        res = parse_definitions(json.dumps(data))
        
        # Verify Function Entry
        self.assertIn("SetState[2]", res["functions"])
        func = res["functions"]["SetState[2]"]
        self.assertEqual(func["name"], "SetState")
        self.assertEqual(func["args"], ["arg1", "arg2"])
        self.assertEqual(func["description"], "Variant description")
        self.assertEqual(func["usage"], "Variant usage")
        self.assertEqual(func["tags"], ["tag1", "tag2"])

        # Verify Shortcut Entry
        self.assertEqual(len(res["shortcuts"]), 1)
        short = res["shortcuts"][0]
        self.assertEqual(short["trigger"], "ife")
        self.assertEqual(short["contents"], "If(Equal(${1}, ${2}))")
        self.assertEqual(short["annotation"], "If Equals")

    def test_overloading_details(self):
        """Ensures different variants of the same function keep their specific metadata."""
        data = {
            "functions": [
                {
                    "name": "Log",
                    "variants": [
                        {"args": ["msg"], "description": "Simple log"},
                        {"args": ["msg", "lvl"], "description": "Level log"}
                    ]
                }
            ]
        }
        res = parse_definitions(json.dumps(data))
        self.assertEqual(res["functions"]["Log[1]"]["description"], "Simple log")
        self.assertEqual(res["functions"]["Log[2]"]["description"], "Level log")

    def test_tag_inheritance(self):
        """Verifies that function-level tags are applied to every variant."""
        data = {
            "functions": [
                {
                    "name": "Func",
                    "tags": ["logic"],
                    "variants": [{"args": ["a"]}, {"args": ["a", "b"]}]
                }
            ]
        }
        res = parse_definitions(json.dumps(data))
        self.assertEqual(res["functions"]["Func[1]"]["tags"], ["logic"])
        self.assertEqual(res["functions"]["Func[2]"]["tags"], ["logic"])

    def test_invalid_json_handling(self):
        empty_state = {"functions": {}, "shortcuts": []}
        self.assertEqual(parse_definitions("not json"), empty_state)
        self.assertEqual(parse_definitions(""), empty_state)
        self.assertEqual(parse_definitions(None), empty_state)

if __name__ == "__main__":
    unittest.main()
