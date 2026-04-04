# tests/test_chapter_info_parser.py
import sys
import os
import unittest
import tempfile

# Add the package root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fa_parser.chapter_info_parser import get_world_file_path

class TestChapterInfoParser(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = self.temp_dir.name

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_get_world_file_path_success(self):
        chapter_info_path = os.path.join(self.dir_path, "chapterInfo.txt")
        world_file_path = os.path.join(self.dir_path, "world.txt")
        
        with open(chapter_info_path, "w", encoding="utf-8") as f:
            f.write('world_file_name = "world.txt"')
            
        with open(world_file_path, "w", encoding="utf-8") as f:
            f.write("dummy data")
            
        res = get_world_file_path(chapter_info_path)
        self.assertEqual(res, world_file_path)

    def test_missing_chapter_info(self):
        res = get_world_file_path(os.path.join(self.dir_path, "missing.txt"))
        self.assertIsNone(res)

    def test_missing_world_file_entry(self):
        chapter_info_path = os.path.join(self.dir_path, "chapterInfo.txt")
        with open(chapter_info_path, "w", encoding="utf-8") as f:
            f.write('some_other_key = "value"')
            
        res = get_world_file_path(chapter_info_path)
        self.assertIsNone(res)

    def test_referenced_world_file_does_not_exist(self):
        chapter_info_path = os.path.join(self.dir_path, "chapterInfo.txt")
        with open(chapter_info_path, "w", encoding="utf-8") as f:
            f.write('world_file_name = "missing.txt"')
            
        res = get_world_file_path(chapter_info_path)
        self.assertIsNone(res)

    def test_get_world_file_path_with_whitespace(self):
        chapter_info_path = os.path.join(self.dir_path, "chapterInfo.txt")
        world_file_path = os.path.join(self.dir_path, "world.txt")
        
        with open(chapter_info_path, "w", encoding="utf-8") as f:
            f.write('   world_file_name   =   "world.txt"   ')
            
        with open(world_file_path, "w", encoding="utf-8") as f:
            f.write("dummy data")
            
        res = get_world_file_path(chapter_info_path)
        self.assertEqual(res, world_file_path)

if __name__ == "__main__":
    unittest.main()
