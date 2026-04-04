# tests/test_cursor_parser.py
import sys
import os
import unittest

# Add the package root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fa_parser.cursor_parser import parse_cursor_position, tokenize

class TestCursorParser(unittest.TestCase):
    def test_tokenize_basic(self):
        line = "Func(a, 1);"
        tokens = tokenize(line)
        
        # Expected tokens: word(Func), (, word(a), ,, word(1), )
        # (Note: space at index 7 and semicolon at index 10 are skipped)
        expected = [
            ("word", "Func", 0, 4),
            ("(", "(", 4, 5),
            ("word", "a", 5, 6),
            (",", ",", 6, 7),
            ("word", "1", 8, 9),
            (")", ")", 9, 10)
        ]
        
        self.assertEqual(len(tokens), len(expected))
        for i, (ttype, tval, tstart, tend) in enumerate(expected):
            self.assertEqual(tokens[i].type, ttype, "Token {} type".format(i))
            self.assertEqual(tokens[i].value, tval, "Token {} value".format(i))
            self.assertEqual(tokens[i].start, tstart, "Token {} start".format(i))
            self.assertEqual(tokens[i].end, tend, "Token {} end".format(i))

    def test_tokenize_strings_and_escapes(self):
        line = 'Say("Hello \\"World\\"");'
        tokens = tokenize(line)
        
        expected = [
            ("word", "Say", 0, 3),
            ("(", "(", 3, 4),
            ("string", '"Hello \\"World\\""', 4, 21),
            (")", ")", 21, 22)
        ]
        
        self.assertEqual(len(tokens), len(expected))
        for i, (ttype, tval, tstart, tend) in enumerate(expected):
            self.assertEqual(tokens[i].type, ttype, "Token {} type".format(i))
            self.assertEqual(tokens[i].value, tval, "Token {} value".format(i))
            self.assertEqual(tokens[i].start, tstart, "Token {} start".format(i))
            self.assertEqual(tokens[i].end, tend, "Token {} end".format(i))

    def test_tokenize_comments(self):
        line = "Func(); // Some comment"
        tokens = tokenize(line)
        
        expected = [
            ("word", "Func", 0, 4),
            ("(", "(", 4, 5),
            (")", ")", 5, 6),
            ("comment", "// Some comment", 8, len(line))
        ]
        
        self.assertEqual(len(tokens), len(expected))
        for i, (ttype, tval, tstart, tend) in enumerate(expected):
            self.assertEqual(tokens[i].type, ttype, "Token {} type".format(i))
            self.assertEqual(tokens[i].value, tval, "Token {} value".format(i))
            self.assertEqual(tokens[i].start, tstart, "Token {} start".format(i))
            self.assertEqual(tokens[i].end, tend, "Token {} end".format(i))

    def test_parse_cursor_position_basic(self):
        cases = [
            ("SetState(entityTag, stateName);", 4, "SetState", "SetState[2]", None),
            ("SetState(entityTag, stateName);", 12, "SetState", "SetState[2]", 0),
            ("SetState(entityTag, stateName);", 22, "SetState", "SetState[2]", 1),
            ("EndLevel();", 4, "EndLevel", "EndLevel[0]", None),
        ]
        for line, offset, name, fid, arg in cases:
            res = parse_cursor_position(line, offset)
            self.assertEqual(res["function_name"], name)
            self.assertEqual(res["function_id"], fid)
            self.assertEqual(res["arg_index"], arg)

    def test_parse_cursor_position_outside_function(self):
        res = parse_cursor_position("// comment", 5)
        self.assertIsNone(res)

    def test_parse_cursor_position_robustness(self):
        cases = [
            # Strings with commas and parentheses
            ('Say("Hello, (World)");', 1, "Say", "Say[1]", None),
            ('Say("Hello, (World)");', 4, "Say", "Say[1]", 0),
            ('Say("Hello, (World)");', 5, "Say", "Say[1]", 0),
            ('SetState(tag, "val,ue");', 17, "SetState", "SetState[2]", 1),
            
            # Escaped quotes in strings
            ('Say("Escaped \\" quote");', 5, "Say", "Say[1]", 0),
            
            # Comments
            ('SetState(1, 2); // SetState(3, 4)', 25, None, None, None),
            
            # Complex nesting with strings
            ('If(Equal("a,b", "c)d"))', 2, "If", "If[1]", None),
            ('If(Equal("a,b", "c)d"))', 3, "If", "If[1]", 0),
            ('If(Equal("a,b", "c)d"))', 9, "Equal", "Equal[2]", 0),
            ('If(Equal("a,b", "c)d"))', 11, "Equal", "Equal[2]", 0),
            ('If(Equal("a,b", "c)d"))', 18, "Equal", "Equal[2]", 1),
        ]
        for line, offset, name, fid, arg in cases:
            res = parse_cursor_position(line, offset)
            if name is None:
                self.assertIsNone(res, "Expected None for line '{}' at offset {}".format(line, offset))
            else:
                self.assertIsNotNone(res, "Expected result for line '{}' at offset {}".format(line, offset))
                self.assertEqual(res["function_name"], name, "Line '{}' offset {}".format(line, offset))
                self.assertEqual(res["function_id"], fid, "Line '{}' offset {}".format(line, offset))
                self.assertEqual(res["arg_index"], arg, "Line '{}' offset {}".format(line, offset))

    def test_parse_cursor_position_empty(self):
        cases = [
            ("TriggerEvent()", 13, "TriggerEvent", "TriggerEvent[1]", 0),
            ("SetLightState(,)", 13, "SetLightState", "SetLightState[2]", None),
            ("SetLightState(,)", 14, "SetLightState", "SetLightState[2]", 0),
            ("SetLightState( ,)", 14, "SetLightState", "SetLightState[2]", 0),
            ("SetLightState( ,)", 15, "SetLightState", "SetLightState[2]", 0),
            ("SetLightState( ,)", 16, "SetLightState", "SetLightState[2]", 1),
            ("SetLightState( , )", 16, "SetLightState", "SetLightState[2]", 1),
        ]
        for line, offset, name, fid, arg in cases:
            res = parse_cursor_position(line, offset)
            self.assertEqual(res["function_name"], name)
            self.assertEqual(res["function_id"], fid)
            self.assertEqual(res["arg_index"], arg)

    def test_parse_cursor_position_nested(self):
        line = "If(Equal(name, value))"
        
        # 1. Cursor on "If"
        res = parse_cursor_position(line, 1)
        self.assertEqual(res["function_name"], "If")
        self.assertEqual(res["function_id"], "If[1]")
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

    def test_parse_cursor_position_edge_cases(self):
        cases = [
            # Spaces between function name and parenthesis
            # S e t S t a t e     ( t a g ,   v a l u e ) ;
            # 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2
            ("SetState  (tag, value);", 10, "SetState", "SetState[2]", None), # right before (
            ("SetState  (tag, value);", 11, "SetState", "SetState[2]", 0),    # right after (
            ("SetState  (tag, value);", 12, "SetState", "SetState[2]", 0),    # on 't'
            
            # Multiple calls on the same line
            # F u n c 1 ( a ) ;   F u n c 2 ( b ,   c ) ;
            # 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
            ("Func1(a); Func2(b, c);", 6, "Func1", "Func1[1]", 0),    # after Func1(
            ("Func1(a); Func2(b, c);", 7, "Func1", "Func1[1]", 0),    # on 'a'
            ("Func1(a); Func2(b, c);", 16, "Func2", "Func2[2]", 0),    # after Func2(
            ("Func1(a); Func2(b, c);", 17, "Func2", "Func2[2]", 0),    # on 'b'
            ("Func1(a); Func2(b, c);", 19, "Func2", "Func2[2]", 1),    # on 'c'
            
            # Cursor on the comma
            # S e t S t a t e ( t a g ,   v a l u e ) ;
            # 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0
            # S(0)e(1)t(2)S(3)t(4)a(5)t(6)e(7)((8) t(9)a(10)g(11),(12)
            ("SetState(tag, value);", 13, "SetState", "SetState[2]", 1), # gap AFTER ,
            
            # Empty arguments
            ("Func();", 5, "Func", "Func[1]", 0),
        ]
        for line, offset, name, fid, arg in cases:
            res = parse_cursor_position(line, offset)
            msg = "Failed on line '{}' at offset {}".format(line, offset)
            self.assertIsNotNone(res, msg)
            self.assertEqual(res["function_name"], name, msg)
            self.assertEqual(res["function_id"], fid, msg)
            self.assertEqual(res["arg_index"], arg, msg)

if __name__ == "__main__":
    unittest.main()
