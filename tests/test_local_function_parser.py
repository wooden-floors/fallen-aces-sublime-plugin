# tests/test_local_function_parser.py
import sys
import os
import unittest
from unittest.mock import MagicMock

# Add the package root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fa_parser.local_function_parser import discover_local_functions
from tests.test_fallen_aces import FakeView, FakeRegion

class TestLocalFunctionParser(unittest.TestCase):
    def test_discover_local_functions_basic(self):
        # Setup a view with some functions
        # The selector simulation is the key here. 
        # In our FakeView, we need to mock find_by_selector.
        view = FakeView("Func1(a, b); Func2();")
        
        # Manually mock the regions that would be found by the syntax highlighter
        # "Func1" is at 0:5
        # "Func2" is at 13:18
        view.find_by_selector = MagicMock(return_value=[
            FakeRegion(0, 5),
            FakeRegion(13, 18)
        ])
        
        funcs = discover_local_functions(view)
        
        self.assertIn("Func1", funcs)
        self.assertEqual(funcs["Func1"], ["a", "b"])
        
        self.assertIn("Func2", funcs)
        self.assertEqual(funcs["Func2"], [])

    def test_discover_local_functions_with_whitespace(self):
        view = FakeView("  MyFunc  (  arg1 , arg2  )  ")
        view.find_by_selector = MagicMock(return_value=[FakeRegion(2, 8)])
        
        funcs = discover_local_functions(view)
        self.assertEqual(funcs["MyFunc"], ["arg1", "arg2"])

    def test_no_functions_found(self):
        view = FakeView("no functions here")
        view.find_by_selector = MagicMock(return_value=[])
        
        funcs = discover_local_functions(view)
        self.assertEqual(funcs, {})

if __name__ == "__main__":
    unittest.main()
