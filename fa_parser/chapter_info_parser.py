# fa_parser/chapter_info_parser.py
import re
import os

# Regex to find the world file name in chapterInfo.txt
RE_WORLD_FILE = re.compile(r'world_file_name\s*=\s*"(.*?)"')

def get_world_file_path(chapter_info_path):
    """
    Reads chapterInfo.txt and returns the absolute path to the world file.
    Returns None if not found or if the world file doesn't exist.
    """
    if not os.path.exists(chapter_info_path):
        return None

    world_file_name = None
    try:
        with open(chapter_info_path, "r", encoding="utf-8") as f:
            for line in f:
                match = RE_WORLD_FILE.match(line.strip())
                if match:
                    world_file_name = match.group(1)
                    break
    except Exception:
        return None

    if not world_file_name:
        return None

    world_file_path = os.path.join(os.path.dirname(chapter_info_path), world_file_name)
    if not os.path.exists(world_file_path):
        return None

    return world_file_path
