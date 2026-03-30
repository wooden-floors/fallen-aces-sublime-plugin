# tests/test_world_data_provider.py
import sys
import os
import unittest
import tempfile
import time

# Add the package root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.world_data_provider import WorldDataProvider
from parser.world_parser import WorldData

class TestWorldDataProvider(unittest.TestCase):
    def setUp(self):
        self.provider = WorldDataProvider()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = self.temp_dir.name

    def tearDown(self):
        self.temp_dir.cleanup()

    def create_project_files(self, world_name="world.txt", world_content=""):
        project_file = os.path.join(self.dir_path, "test.sublime-project")
        chapter_info = os.path.join(self.dir_path, "chapterInfo.txt")
        world_file = os.path.join(self.dir_path, world_name)
        
        with open(chapter_info, "w", encoding="utf-8") as f:
            f.write('world_file_name = "{}"'.format(world_name))
            
        with open(world_file, "w", encoding="utf-8") as f:
            f.write(world_content)
            
        return project_file, chapter_info, world_file

    def test_get_world_data_basic(self):
        world_content = 'Tag { name="t1" number=10 }'
        project_file, _, _ = self.create_project_files(world_content=world_content)
        
        info = self.provider.get_world_data(project_file)
        self.assertIsInstance(info, WorldData)
        self.assertIn(10, info.tags)
        self.assertEqual(info.tags[10].name, "t1")

    def test_reload_on_world_file_change(self):
        world_content = 'Tag { name="t1" number=10 }'
        project_file, chapter_info, world_file = self.create_project_files(world_content=world_content)
        
        # First load
        info1 = self.provider.get_world_data(project_file)
        self.assertEqual(len(info1.tags), 1)
        
        # Wait a bit to ensure mtime changes
        time.sleep(0.1)
        
        # Update world file
        with open(world_file, "a", encoding="utf-8") as f:
            f.write('\nTag { name="t2" number=20 }')
            
        # Second load should detect change
        info2 = self.provider.get_world_data(project_file)
        self.assertEqual(len(info2.tags), 2)
        self.assertIn(20, info2.tags)

    def test_reload_on_chapter_info_change(self):
        project_file, chapter_info, _ = self.create_project_files(world_name="v1.txt")
        
        # Create second world file
        world2_path = os.path.join(self.dir_path, "v2.txt")
        with open(world2_path, "w", encoding="utf-8") as f:
            f.write('Tag { name="v2" number=2 }')
            
        # Initial load
        self.provider.get_world_data(project_file)
        
        time.sleep(0.1)
        
        # Point chapterInfo to new world file
        with open(chapter_info, "w", encoding="utf-8") as f:
            f.write('world_file_name = "v2.txt"')
            
        # Should pick up new world file
        info = self.provider.get_world_data(project_file)
        self.assertIn(2, info.tags)
        self.assertEqual(info.tags[2].name, "v2")

    def test_missing_files(self):
        project_file = os.path.join(self.dir_path, "nonexistent.project")
        self.assertIsNone(self.provider.get_world_data(project_file))

if __name__ == "__main__":
    unittest.main()
