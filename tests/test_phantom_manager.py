import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add the package root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tests.sublime_stub
import fa_core.phantom_manager as phantom_manager
from fa_parser.world_parser import Event, Tag, WorldData

class FakeRegion:
    def __init__(self, a, b):
        self._a = a
        self._b = b
    def begin(self): return min(self._a, self._b)
    def end(self): return max(self._a, self._b)
    def __eq__(self, other):
        return self._a == other._a and self._b == other._b

class TestPhantomManager(unittest.TestCase):
    def setUp(self):
        self.manager = phantom_manager.PhantomManager()
        self.view = MagicMock()
        self.view.id.return_value = 123
        self.window = MagicMock()
        self.view.window.return_value = self.window
        
        # Mock settings
        self.settings = {}
        self.view.settings().get.side_effect = lambda k, d=None: self.settings.get(k, d)
        self.view.settings().set.side_effect = self.settings.__setitem__

        # Mock Project Data
        self.project_data = {}
        def set_project_data(data):
            self.project_data.update(data)
            # Propagate to settings to simulate ST behavior for subsequent is_enabled() calls
            s = data.get("settings", {})
            for k, v in s.items():
                self.settings[k] = v
        
        self.window.project_data.side_effect = lambda: self.project_data
        self.window.set_project_data.side_effect = set_project_data

        # Mock PhantomSet
        self.phantom_set_mock = MagicMock()
        with patch("sublime.PhantomSet", return_value=self.phantom_set_mock):
            self.manager.get_phantom_set(self.view)

    def test_is_enabled(self):
        self.settings["fallen_aces_show_phantoms"] = True
        self.assertTrue(self.manager.is_enabled(self.view))
        
        self.settings["fallen_aces_show_phantoms"] = False
        self.assertFalse(self.manager.is_enabled(self.view))

    def test_toggle(self):
        self.settings["fallen_aces_show_phantoms"] = False
        self.project_data = {}
        with patch.object(self.manager, 'refresh') as mock_refresh:
            res = self.manager.toggle(self.view)
            self.assertTrue(res)
            self.assertEqual(self.project_data.get("settings", {}).get("fallen_aces_show_phantoms"), True)
            mock_refresh.assert_called_once_with(self.view)

        with patch.object(self.manager, 'clear') as mock_clear:
            res = self.manager.toggle(self.view)
            self.assertFalse(res)
            self.assertEqual(self.project_data.get("settings", {}).get("fallen_aces_show_phantoms"), False)
            mock_clear.assert_called_once_with(self.view)

    def test_clear(self):
        self.manager.clear(self.view)
        self.phantom_set_mock.update.assert_called_once_with([])

    @patch("sublime.set_timeout_async")
    def test_refresh_debounced(self, mock_timeout):
        self.settings["fallen_aces_show_phantoms"] = True
        self.manager.refresh_debounced(self.view, delay=500)
        
        mock_timeout.assert_called_once()
        callback = mock_timeout.call_args[0][0]
        delay = mock_timeout.call_args[0][1]
        
        self.assertEqual(delay, 500)
        
        # Verify it calls _do_refresh when callback is executed
        with patch.object(self.manager, '_do_refresh') as mock_do_refresh:
            callback()
            mock_do_refresh.assert_called_once_with(self.view)

    @patch("fa_core.world_data_provider.provider.get_world_data")
    @patch("fa_core.definition_provider.provider.get_function_definitions")
    @patch("fa_core.definition_provider.provider.get_hardcoded_suggestions")
    @patch("sublime.Region", side_effect=FakeRegion)
    @patch("sublime.Phantom")
    def test_do_refresh(self, mock_phantom, mock_region, mock_hardcoded, mock_defs, mock_world):
        self.settings["fallen_aces_show_phantoms"] = True
        
        # Setup data
        mock_world.return_value = WorldData(
            events={101: Event("MyEvent", 101)},
            tags={50: Tag("MyTag", 50)},
            things={}
        )
        mock_defs.return_value = {
            "TriggerEvent[1]": {"name": "TriggerEvent", "args": ["eventNumber"]},
            "SetState[2]": {"name": "SetState", "args": ["entityTag", "state"]}
        }
        mock_hardcoded.return_value = {
            "state": {"1": "Active"}
        }

        # Setup view content
        self.view.size.return_value = 100
        line1 = "TriggerEvent(101);"
        line2 = "SetState(50, 1);"
        
        # Mock view.lines to return regions for our lines
        self.view.lines.return_value = [FakeRegion(0, len(line1)), FakeRegion(len(line1)+1, len(line1)+1+len(line2))]
        
        def mock_substr(reg):
            if reg.begin() == 0: return line1
            return line2
        self.view.substr.side_effect = mock_substr
        
        self.manager._do_refresh(self.view)
        
        # Check phantoms created
        # 1. Event hint for 101
        # 2. Tag hint for 50
        # 3. Hardcoded hint for 1
        self.assertEqual(mock_phantom.call_count, 3)
        
        # Verify some phantom contents
        calls = mock_phantom.call_args_list
        # TriggerEvent(101) -> MyEvent
        self.assertIn("MyEvent", calls[0][0][1])
        # SetState(50, 1) -> MyTag
        self.assertIn("MyTag", calls[1][0][1])
        # SetState(50, 1) -> Active
        self.assertIn("Active", calls[2][0][1])

        # Verify phantom_set.update was called with the phantoms
        self.phantom_set_mock.update.assert_called_once()
        phantoms_passed = self.phantom_set_mock.update.call_args[0][0]
        self.assertEqual(len(phantoms_passed), 3)

    def test_do_refresh_disabled(self):
        self.settings["fallen_aces_show_phantoms"] = False
        with patch.object(self.manager, 'get_phantom_set') as mock_get_set:
            self.manager._do_refresh(self.view)
            mock_get_set.assert_not_called()

if __name__ == "__main__":
    unittest.main()
