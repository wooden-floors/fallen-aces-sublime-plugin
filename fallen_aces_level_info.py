import os
import re

PROJECT_STRUCTURE_CACHE = {}
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

    if project_file_name not in PROJECT_STRUCTURE_CACHE:
        _log("Project structure is not cached for {}".format(project_file_name))
        PROJECT_STRUCTURE_CACHE[project_file_name] = _read_project_structure(project_file_name)

    chapter_info_path = PROJECT_STRUCTURE_CACHE[project_file_name]["chapterInfoPath"]
    chapter_info_last_reload_time = PROJECT_STRUCTURE_CACHE[project_file_name]["chapterInfoLastReloadTime"]

    chapter_info_last_modification_time = os.path.getmtime(chapter_info_path)

    if chapter_info_last_reload_time == None or chapter_info_last_reload_time < chapter_info_last_modification_time:
        _log("Should reload level info path. chapterInfo.txt last reload - {}, last update - {}".format(chapter_info_last_reload_time, chapter_info_last_modification_time))
        PROJECT_STRUCTURE_CACHE[project_file_name]["levelInfoPath"] = _read_level_info_path(chapter_info_path)
        PROJECT_STRUCTURE_CACHE[project_file_name]["levelInfoLastReloadTime"] = None
        PROJECT_STRUCTURE_CACHE[project_file_name]["chapterInfoLastReloadTime"] = chapter_info_last_modification_time

    level_info_path = PROJECT_STRUCTURE_CACHE[project_file_name]["levelInfoPath"]
    level_info_last_reload_time = PROJECT_STRUCTURE_CACHE[project_file_name]["levelInfoLastReloadTime"]

    level_info_last_modification_time = os.path.getmtime(level_info_path)
    if level_info_last_reload_time == None or level_info_last_reload_time < level_info_last_modification_time:
        _log("Should reload level info. levelInfo last reload - {}, last update - {}".format(level_info_last_reload_time, level_info_last_modification_time))
        PROJECT_STRUCTURE_CACHE[project_file_name]["levelInfo"] = _read_level_info(level_info_path)
        PROJECT_STRUCTURE_CACHE[project_file_name]["levelInfoLastReloadTime"] = level_info_last_modification_time

    return PROJECT_STRUCTURE_CACHE[project_file_name]["levelInfo"]

def _read_project_structure(project_file_name):
    _log("Read project structure for file {}".format(project_file_name))

    folder = os.path.dirname(project_file_name)
    _log("Level folder: {}".format(folder))

    chapter_info_path = os.path.join(folder, "chapterInfo.txt")
    if not os.path.exists(chapter_info_path):
        _log("File doesn't exist: {}".format(chapter_info_path))
        return None

    return {
        "chapterInfoPath": chapter_info_path,
        "chapterInfoLastReloadTime": None
    }

def _read_level_info_path(chapter_info_path):
    with open(chapter_info_path, "r", encoding="utf-8") as f:
        for line in f:
            match = re.match(r'world_file_name\s*=\s*"(.*?)"', line.strip())
            if match:
                level_file_name = match.group(1)
                break

    if not level_file_name:
        _log("Can't find world file name in chapterInfo.txt")
        return None

    folder = os.path.dirname(chapter_info_path)
    level_file_path = os.path.join(folder, level_file_name)
    if not os.path.exists(level_file_path):
        _log("File doesn't exist: {}".format(level_file_path))
        return None

    return level_file_path

def _read_level_info(level_file_path):
    _log("Reading level info")
    raw_level_info = open(level_file_path, "r", encoding="utf-8").read()
    level_info = _parse_level_info(raw_level_info)

    _log("Parsed data: {}".format(level_info))
    return level_info

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
    
    things = {}
    thing_blocks = re.findall(r'Thing\b[^\{]*\{(.*?)\}', raw_level_info, flags=re.DOTALL)
    _log("Found {} things".format(len(thing_blocks)))
    for block in thing_blocks:
        definition_id = _extract_int(block, "definition_id")
        tag = _extract_int(block, "tag")
        if definition_id and tag:
            things.setdefault(definition_id, []).append(tag)

    return {
        "events": events,
        "tags": tags,
        "things": things
    }

def _extract_string(block, field_name):
    pattern = r'{}\s*=\s*"(.*?)"'.format(field_name)
    match = re.search(pattern, block)
    return match.group(1) if match else None

def _extract_int(block, field_name):
    pattern = r'{}\s*=\s*(\d+)'.format(field_name)
    m = re.search(pattern, block)
    return int(m.group(1)) if m else None
