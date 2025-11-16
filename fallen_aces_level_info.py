import os
import re

LEVEL_INFO_CACHE = {}
DEBUG_ENABLED = False

def _log(msg):
    if DEBUG_ENABLED:
        print("[LEVEL INFO]: {}".format(msg))

def get_level_info(view):
    global DEBUG_ENABLED 
    DEBUG_ENABLED = view.settings().get("fallen_aces_plugin_debug_enabled")

    window = view.window()
    if not window:
        return None

    project_file_name = window.project_file_name()
    if not project_file_name:
        return None

    if project_file_name in LEVEL_INFO_CACHE:
        _log("Get cached level info")
        return LEVEL_INFO_CACHE[project_file_name]

    level_info = _read_level_info(project_file_name)
    _log("Parsed data: {}".format(level_info))
    
    LEVEL_INFO_CACHE[project_file_name] = level_info
    return level_info

def _read_level_info(project_file_name):
    _log("Reading level info")

    raw_level_info = _read_raw_level_info(project_file_name)
    return _parse_level_info(raw_level_info)

def _read_raw_level_info(project_file_name):
    folder = os.path.dirname(project_file_name)
    _log("Level folder: {}".format(folder))

    chapter_info_path = os.path.join(folder, "chapterInfo.txt")
    if not os.path.exists(chapter_info_path):
        _log("File doesn't exist: {}".format(chapter_info_path))
        return None

    world_file_name = None
    with open(chapter_info_path, "r", encoding="utf-8") as f:
        for line in f:
            match = re.match(r'world_file_name\s*=\s*"(.*?)"', line.strip())
            if match:
                world_file_name = match.group(1)
                break
    if not world_file_name:
        _log("Can't find world file name in chapterInfo.txt")
        return None

    world_file_path = os.path.join(folder, world_file_name)
    if not os.path.exists(world_file_path):
        _log("File doesn't exist: {}".format(world_file_path))
        return None

    return open(world_file_path, "r", encoding="utf-8").read()

def _parse_level_info(raw_level_info):
    if not raw_level_info:
        _log("Empty level info")
        return None

    events = {}
    event_blocks = re.findall(r'Event\s*\{(.*?)\}', raw_level_info, flags=re.DOTALL)
    for block in event_blocks:
        name = _extract_string(block, "name")
        number = _extract_int(block, "number")
        if name and number:
            events[number] = '{} - {}'.format(name, number)

    tags = {}
    tag_blocks = re.findall(r'Tag\s*\{(.*?)\}', raw_level_info, flags=re.DOTALL)
    for block in tag_blocks:
        name = _extract_string(block, "name")
        number = _extract_int(block, "number")
        if name and number:
            tags[number] = '{} - {}'.format(name, number)
    
    return {
        "events": events,
        "tags": tags
    }

def _extract_string(block, field_name):
    pattern = r'{}\s*=\s*"(.*?)"'.format(field_name)
    match = re.search(pattern, block)
    return match.group(1) if match else None

def _extract_int(block, field_name):
    pattern = r'{}\s*=\s*(\d+)'.format(field_name)
    m = re.search(pattern, block)
    return int(m.group(1)) if m else None
