import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fa_parser.world_parser import parse_world_file, WorldData


class TestWorldParser(unittest.TestCase):
    
    def test_basic(self):
        raw = """
        Global 
        { 
            editor_version_major = 0; 
            timestamp = "12/16/2025 16:10:20"; 
        }
        Event 
        { 
            name = "e1"; 
            number = 1; 
        } 
        Tag 
        { 
            name = "t1"; 
            number = 10; 
        } 
        Thing 
        { 
            definition_id = 517; 
            tag = 10; 
        }
        LayerInfo 
        { 
            id = 0; 
            name = "0: BASE"; 
        }
        """
        data = parse_world_file(raw)
        
        self.assertIsInstance(data, WorldData)
        self.assertEqual(data.events[1].name, "e1")
        self.assertEqual(data.tags[10].name, "t1")
        self.assertIn(10, data.things[517])

    def test_formatting(self):
        test_cases = [
        """
        Event 
        { 
            name = "e1"; 
            number = 1; 
        }
        """,
        """
        Event 
        { 
            name = "e1"
            number = 1
        }
        """,
        """
                Event 
        { 
            name = "e1"; 
        number = 1; 
        }
        """,
        """
        Event 
        { 
        name = "e1"; 
        number = 1; 
        }
        """,
        """
        Event { 
            name = "e1"; 
            number = 1; 
        }
        """,
        """ 
        Event{ 
            name = "e1"; 
            number = 1; 
        }
        """,
        """
        Event { name = "e1"; number = 1; }
        """
        ]

        for raw in test_cases:
            data = parse_world_file(raw)
        
            self.assertIsInstance(data, WorldData)
            self.assertEqual(data.events[1].name, "e1")

    def test_malformed_blocks(self):
        """Should skip incomplete blocks."""
        raw = 'Event { name="no-number" } Thing { tag=5 }'
        data = parse_world_file(raw)
        self.assertEqual(len(data.events), 0)
        self.assertEqual(len(data.things), 0)

    def test_multiple_blocks(self):
        """Should correctly parse multiple instances of each block type."""
        raw = """
        Event { name="e1" number=1 }
        Event { name="e2" number=2 }
        Tag { name="t1" number=100 }
        Tag { name="t2" number=200 }
        Thing { definition_id=500 tag=10 }
        Thing { definition_id=500 tag=11 }
        Thing { definition_id=600 tag=20 }
        """
        data = parse_world_file(raw)
        
        self.assertIsInstance(data, WorldData)
        self.assertEqual(data.events[1].name, "e1")
        self.assertEqual(data.events[2].name, "e2")

        self.assertEqual(data.tags[100].name, "t1")
        self.assertEqual(data.tags[200].name, "t2")

        self.assertIn(10, data.things[500])
        self.assertIn(11, data.things[500])
        self.assertIn(20, data.things[600])

    def test_empty_input(self):
        self.assertIsNone(parse_world_file(""))
        self.assertIsNone(parse_world_file(None))

if __name__ == "__main__":
    unittest.main()
