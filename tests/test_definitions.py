# tests/test_definitions.py
import sys
import os
import unittest
import json

# Add the package root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fa_core.definition_provider import DefinitionProvider, provider as global_provider

class TestDefinitions(unittest.TestCase):
    def setUp(self):
        # Use a fresh instance for every test to ensure total isolation 
        self.provider = DefinitionProvider()

    def test_singleton_instance(self):
        """Verifies that the global provider is indeed a DefinitionProvider."""
        self.assertIsInstance(global_provider, DefinitionProvider)

    def test_lazy_loading_logic(self):
        """
        Verifies that data is only loaded when requested and then cached.
        """
        load_count = {"count": 0}
        def mock_loader():
            load_count["count"] += 1
            return '{"functions": [{"name": "F1", "variants": [{"args": []}]}]}'
        
        self.provider.set_loader(mock_loader)
        self.assertEqual(load_count["count"], 0)
        
        # First call triggers load
        defs = self.provider.get_function_definitions()
        self.assertIn("F1[0]", defs)
        self.assertEqual(load_count["count"], 1)
        
        # Second call uses cache
        self.provider.get_function_definitions()
        self.assertEqual(load_count["count"], 1)

    def test_clear_cache_forces_reload(self):
        """Verifies that clear_cache allows a fresh load."""
        load_count = {"count": 0}
        def mock_loader():
            load_count["count"] += 1
            return '{}'
            
        self.provider.set_loader(mock_loader)
        self.provider.get_shortcuts()
        self.assertEqual(load_count["count"], 1)
        
        self.provider.clear_cache()
        self.provider.get_shortcuts()
        self.assertEqual(load_count["count"], 2)

    def test_empty_json_handling(self):
        """Verifies safety when keys are missing from a valid JSON object."""
        self.provider.set_loader(lambda: "{}")
        self.assertEqual(self.provider.get_function_definitions(), {})
        self.assertEqual(self.provider.get_shortcuts(), [])

if __name__ == "__main__":
    unittest.main()
