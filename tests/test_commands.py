import sys
import os
# Add the package root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from unittest.mock import MagicMock, patch

# Mock sublime and sublime_plugin before importing fallen_aces
import tests.sublime_stub
import sublime
import sublime_plugin

import fallen_aces

class TestCommands(unittest.TestCase):

    def setUp(self):
        self.window = MagicMock()
        self.view = MagicMock()
        # FallenAcesToggleAutoSyntaxCommand is a WindowCommand
        self.auto_syntax_cmd = fallen_aces.FallenAcesToggleAutoSyntaxCommand(self.window)
        # FallenAcesToggleDebugLoggingCommand is a WindowCommand
        self.debug_logging_cmd = fallen_aces.FallenAcesToggleDebugLoggingCommand(self.window)

    @patch("sublime.status_message")
    def test_toggle_auto_syntax_enables(self, mock_status):
        self.window.project_data.return_value = {"settings": {}}
        
        self.auto_syntax_cmd.run()
        
        self.window.set_project_data.assert_called_once()
        data = self.window.set_project_data.call_args[0][0]
        self.assertTrue(data["settings"]["fallen_aces_auto_syntax_enabled"])
        mock_status.assert_called_with("Fallen Aces Auto Syntax: Enabled")

    @patch("sublime.status_message")
    def test_toggle_auto_syntax_disables(self, mock_status):
        self.window.project_data.return_value = {
            "settings": {"fallen_aces_auto_syntax_enabled": True}
        }
        
        self.auto_syntax_cmd.run()
        
        data = self.window.set_project_data.call_args[0][0]
        self.assertFalse(data["settings"]["fallen_aces_auto_syntax_enabled"])
        mock_status.assert_called_with("Fallen Aces Auto Syntax: Disabled")

    @patch("sublime.status_message")
    @patch("fallen_aces.logger.set_enabled")
    def test_toggle_debug_logging(self, mock_logger_set, mock_status):
        self.window.project_data.return_value = {"settings": {}}
        
        self.debug_logging_cmd.run()
        
        data = self.window.set_project_data.call_args[0][0]
        self.assertTrue(data["settings"]["fallen_aces_plugin_debug_enabled"])
        mock_logger_set.assert_called_with(True)
        mock_status.assert_called_with("Fallen Aces Debug Logging: Enabled")

    @patch("sublime.error_message")
    def test_toggle_no_project(self, mock_error):
        self.window.project_data.return_value = None
        
        self.auto_syntax_cmd.run()
        
        mock_error.assert_called()
        self.window.set_project_data.assert_not_called()

if __name__ == "__main__":
    unittest.main()
