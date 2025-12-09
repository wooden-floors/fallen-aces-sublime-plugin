import sublime
import sublime_plugin
import os
import re
import html
import json


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
DEBUG_ENABLED = False

def _debug(msg):
    if DEBUG_ENABLED:
        print("[FallenAcesPlugin]: {}".format(msg))


def _check_debug_enabled_flag(view):
    global DEBUG_ENABLED
    DEBUG_ENABLED = view.settings().get("fallen_aces_plugin_debug_enabled", False)


# ---------------------------------------------------------------------------
# Cursor parsing
# ---------------------------------------------------------------------------

def get_cursor_position(view, point):
    """
    Extracts the current line and cursor offset from the Sublime view,
    then delegates to parse_cursor_position.
    """
    line_region = view.line(point)
    line = view.substr(line_region)
    cursor_offset = point - line_region.begin()
    return parse_cursor_position(line, cursor_offset)


def parse_cursor_position(line, cursor_offset):
    """
    Given a line of text and a cursor offset within that line, returns a dict 
    describing which function call the cursor is inside and which argument it is on. 
    
    Returns None if the cursor is not inside a function call.

    Example return value:
        {
            "function_id":   "SetState[2]",  # name + arg count
            "function_name": "SetState",
            "arg_index":     0,              # None if cursor is on the function name
        }
    """
    _debug("parse_cursor_position - line='{}', cursor_offset={}".format(line, cursor_offset))

    # 1. Find all function candidates (word followed by '(')
    candidates = []
    for match in re.finditer(r'\b(\w+)\s*\(', line):
        func_name = match.group(1)
        func_start = match.start()
        args_start = match.end() # Right after '('
        
        # Find matching ')'
        stack = 1
        func_end = -1
        for i in range(args_start, len(line)):
            if line[i] == '(':
                stack += 1
            elif line[i] == ')':
                stack -= 1
                if stack == 0:
                    func_end = i
                    break
        
        if func_end != -1:
            candidates.append({
                "name": func_name,
                "start": func_start,
                "args_start": args_start,
                "end": func_end
            })

    # 2. Filter candidates that contain the cursor
    # We want the innermost function, which is the one with the latest start position.
    active_func = None
    for cand in candidates:
        if cand["start"] <= cursor_offset <= cand["end"]:
            if active_func is None or cand["start"] > active_func["start"]:
                active_func = cand

    if not active_func:
        _debug("parse_cursor_position - no active function at cursor, return")
        return None

    _debug("parse_cursor_position - active_func={}".format(active_func))

    # 3. Determine if cursor is on the name or inside arguments
    if cursor_offset < active_func["args_start"]:
        _debug("parse_cursor_position - cursor on function name")
        arg_index = None
    else:
        # Cursor is inside arguments. Count commas at the top-level of THIS function.
        arg_index = 0
        stack = 0
        args_text = line[active_func["args_start"]:active_func["end"]]
        relative_cursor = cursor_offset - active_func["args_start"]

        for i, char in enumerate(args_text):
            if i >= relative_cursor:
                break
            if char == '(':
                stack += 1
            elif char == ')':
                stack -= 1
            elif char == ',' and stack == 0:
                arg_index += 1
        
        _debug("parse_cursor_position - arg_index={}".format(arg_index))

    # 4. Determine total argument count for the function_id
    total_args = 0
    args_text = line[active_func["args_start"]:active_func["end"]].strip()
    if args_text:
        total_args = 1
        stack = 0
        for char in args_text:
            if char == '(':
                stack += 1
            elif char == ')':
                stack -= 1
            elif char == ',' and stack == 0:
                total_args += 1

    result = {
        "function_id": "{}[{}]".format(active_func["name"], total_args),
        "function_name": active_func["name"],
        "arg_index": arg_index,
    }
    _debug("parse_cursor_position - result={}".format(result))
    return result

# ---------------------------------------------------------------------------
# Metadata loading
# ---------------------------------------------------------------------------

# Note: this cache is never invalidated. If you update fallen-aces-data.json,
# restart Sublime Text to pick up the changes.
_METADATA_CACHE = {}

def _get_metadata():
    """
    Returns metadata: function definitions & short cuts.
    On first call loads and parses metadata from fallen-aces-data.json.
    """
    global _METADATA_CACHE

    if _METADATA_CACHE:
        _debug("_get_metadata - return cached metadata")
        return _METADATA_CACHE

    data = load_plugin_resource("fallen-aces-data.json")
    if not data:
        _debug("_get_metadata - could not load data, return")
        return {}
    
    try:
        json_data = json.loads(data)
    except Exception as e:
        _debug("_get_metadata - error parsing JSON: {}, return".format(e))
        return {}

    functions = {}
    for func in json_data.get("functions", []):
        name = func["name"]
        tags = func.get("tags", [])
        for variant in func.get("variants", []):
            args = variant.get("args", [])
            func_id = "{}[{}]".format(name, len(args))
            functions[func_id] = {
                "name": name,
                "args": args,
                "description": variant.get("description"),
                "usage": variant.get("usage"),
                "tags": tags
            }

    _METADATA_CACHE = {
        "functions": functions,
        "shortcuts": json_data.get("shortcuts", [])
    }
    
    _debug("_get_metadata - loaded {} function variants and {} shortcuts".format(
        len(_METADATA_CACHE["functions"]), len(_METADATA_CACHE["shortcuts"])))

    return _METADATA_CACHE


def get_function_definitions():
    return _get_metadata().get("functions", {})


def get_shortcuts():
    return _get_metadata().get("shortcuts", [])

def load_plugin_resource(file_name):
    """
    Reads file from the plugin folder.
    """
    path = os.path.join(sublime.packages_path(), "FallenAces", file_name)
    if not os.path.exists(path):
        _debug("load_plugin_resource - file {} doesn't exist, return".format(path))
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

# ---------------------------------------------------------------------------
# UI Helpers
# ---------------------------------------------------------------------------

def format_hint_html(definition):
    """
    Formats a function definition into an HTML hint suitable for popups.
    """
    name = definition["name"]
    args = definition["args"]
    description = definition.get("description")
    usage = definition.get("usage")

    html_content = []
    html_content.append("<b>{}({})</b>".format(name, ", ".join(args)))
    
    if description:
        html_content.append("<div style='margin-top: 5px;'>{}</div>".format(html.escape(description).replace("\n", "<br>")))
    
    if usage:
        html_content.append("<br><b>How to use</b>")
        html_content.append("<div style='background-color:#272822;color:#f8f8f2;padding:8px;margin-top:5px;border-radius:4px;font-family:monospace;'>{}</div>".format(
            html.escape(usage).replace("\n", "<br>").replace(" ", "&nbsp;")
        ))

    return "".join(html_content)

# ---------------------------------------------------------------------------
# Level info
# ---------------------------------------------------------------------------

# Note: this cache invalidates when chapterInfo.txt or the world file changes on disk.
_PROJECT_STRUCTURE_CACHE = {}

def get_level_info(view):
    window = view.window()
    if not window:
        _debug("get_level_info - no window, return")
        return None

    project_file = window.project_file_name()
    if not project_file:
        _debug("get_level_info - no project file, return")
        return None

    return get_project_level_info(project_file)

def get_project_level_info(project_file):
    """
    Returns level info (events, tags, etc) for given project. 
    Returns None if expected files are missing.
    """
    global _PROJECT_STRUCTURE_CACHE

    if project_file not in _PROJECT_STRUCTURE_CACHE:
        _debug("get_project_level_info - project file is not in cache")

        folder = os.path.dirname(project_file)
        chapter_info_path = os.path.join(folder, "chapterInfo.txt")

        if not os.path.exists(chapter_info_path):
            _debug("get_project_level_info - chapterInfo.txt not found in {}, return".format(folder))
            return None
        else:
            _PROJECT_STRUCTURE_CACHE[project_file] = {
                "chapterInfoPath": chapter_info_path
            }

    cache = _PROJECT_STRUCTURE_CACHE[project_file]
    
    chapter_info_path = cache["chapterInfoPath"]
    chapter_info_mtime = os.path.getmtime(chapter_info_path)

    if cache.get("chapterInfoLastReloadTime") is None or cache["chapterInfoLastReloadTime"] < chapter_info_mtime:
        _debug("get_project_level_info - reload world file path from chapterInfo.txt")
        cache["worldFilePath"] = read_world_file_path(chapter_info_path)
        cache["worldFileLastReloadTime"] = None
        cache["chapterInfoLastReloadTime"] = chapter_info_mtime

    world_file_path = cache["worldFilePath"]
    if not world_file_path:
        return None

    world_file_mtime = os.path.getmtime(world_file_path)

    if cache.get("worldFileLastReloadTime") is None or cache["worldFileLastReloadTime"] < world_file_mtime:
        _debug("get_project_level_info - reload level info from world file")
        with open(world_file_path, "r", encoding="utf-8") as f:
            cache["levelInfo"] = parse_level_info(f.read())
        cache["worldFileLastReloadTime"] = world_file_mtime

    _debug("get_project_level_info - return cached level info")
    return cache["levelInfo"]

def parse_level_info(raw):
    """
    Parses the contents of a level world file and returns a dict with three keys:

        events: {number: "name - number"}
        tags:   {number: "name - number"}
        things: {definition_id: [tag, ...]}

    Returns None if the input is empty.
    """
    if not raw:
        _debug("parse_level_info - empty input, return")
        return None

    events = {}
    for block in re.findall(r'Event\s*\{(.*?)\}', raw, flags=re.DOTALL):
        name = _extract_string(block, "name")
        number = _extract_int(block, "number")
        if name and number:
            events[number] = '{} - {}'.format(name, number)

    tags = {}
    for block in re.findall(r'Tag\s*\{(.*?)\}', raw, flags=re.DOTALL):
        name = _extract_string(block, "name")
        number = _extract_int(block, "number")
        if name and number:
            tags[number] = '{} - {}'.format(name, number)

    things = {}
    for block in re.findall(r'Thing\b[^\{]*\{(.*?)\}', raw, flags=re.DOTALL):
        definition_id = _extract_int(block, "definition_id")
        tag = _extract_int(block, "tag")
        if definition_id and tag:
            things.setdefault(definition_id, []).append(tag)

    result = {"events": events, "tags": tags, "things": things}
    _debug("parse_level_info - result={}".format(result))
    return result


def _extract_string(block, field_name):
    match = re.search(r'{}\s*=\s*"(.*?)"'.format(field_name), block)
    return match.group(1) if match else None


def _extract_int(block, field_name):
    match = re.search(r'{}\s*=\s*(\d+)'.format(field_name), block)
    return int(match.group(1)) if match else None


def read_world_file_path(chapter_info_path):
    """
    Reads chapterInfo.txt and returns the path to the world file.
    """
    world_file_name = None
    with open(chapter_info_path, "r", encoding="utf-8") as f:
        for line in f:
            match = re.match(r'world_file_name\s*=\s*"(.*?)"', line.strip())
            if match:
                world_file_name = match.group(1)
                break

    if not world_file_name:
        _debug("read_world_file_path - chapterInfo.txt doesn't include world_file_name, return")
        return None

    world_file_path = os.path.join(os.path.dirname(chapter_info_path), world_file_name)
    if not os.path.exists(world_file_path):
        _debug("read_world_file_path - file {} doesn't exist, return".format(world_file_path))
        return None

    return world_file_path


# ---------------------------------------------------------------------------
# Listener
# ---------------------------------------------------------------------------

# Maps argument names to the definition_id values used in the level world file
# to identify entities of that type.
_VARIABLE_NAME_TO_DEFINITION_ID = {
    "lightStateTag":      [517],   # LightState
    "lightSourceTag":     [518],   # PointLight
    "movableGeometryTag": [534],   # MovableGeometry
    "moveStateTag":       [521],   # MoveState
    "enemyTag": [
        10001,  # Goon
        10002,  # Pipeguy
        10003,  # PistolGuy
        10004,  # Malone
        10005,  # GoonThug
        10006,  # PipeguyWiseguy
        10009,  # MolotovMook
        10011,  # SnipingMook
        10012,  # ArmedMook
        10014,  # KnifeGuy
        10017,  # MachineGunMook
        10021,  # BigPalooka
    ]
}

# Hardcoded hint/completion values for arguments that don't come from the
# level file (e.g. enum-like parameters with fixed string values).
_HARDCODED_SUGGESTIONS = {
    "disturbanceTypeName": {
        "SomethingTurnedOn":  "SomethingTurnedOn",
        "SomethingTurnedOff": "SomethingTurnedOff",
    },
    "speakThroughRadioSetting": {
        "0": "DontSpeakThroughRadio",
        "1": "SpeakThenPutaway",
        "2": "SpeakButDontPutaway",
        "3": "SpeakButDontShow",
    },
    "logLevel": {
        "0": "Info",
        "1": "Warning",
        "2": "Error",
    }
}


def resolve_hover_hint(word, cursor_position, function_definitions, level_info):
    """
    Given the hovered word, cursor context, and data dicts, returns an HTML hint string or None.
    """
    if not cursor_position:
        _debug("resolve_hover_hint - empty cursor, return")
        return None

    function_id = cursor_position["function_id"]
    function_name = cursor_position["function_name"]

    if function_name == word and function_id in function_definitions:
        _debug("resolve_hover_hint - hover on function name, return hint")
        return format_hint_html(function_definitions[function_id])

    if word.isdigit():
        _debug("resolve_hover_hint - hover on a digit")

        if not level_info:
            _debug("resolve_hover_hint - level info is missing, return")
            return None

        arg_index = cursor_position["arg_index"]
        if arg_index is None:
            _debug("resolve_hover_hint - digit is not a function argument, return")
            return None

        if function_id not in function_definitions:
            _debug("resolve_hover_hint - digit is an argument for unknown function, return")
            return None

        arg_name = function_definitions[function_id]["args"][arg_index]
        number = int(word)

        _debug("resolve_hover_hint - digit {} is an argument {} of predefined function {}".format(number, arg_name, function_id))

        if arg_name == "eventNumber" and number in level_info["events"]:
            hint = level_info["events"][number]
            _debug("resolve_hover_hint - digit {} is an event, return hint '{}'".format(number, hint))
            return hint

        if arg_name in _HARDCODED_SUGGESTIONS:
            hint = _HARDCODED_SUGGESTIONS[arg_name].get(word)
            _debug("resolve_hover_hint - digit {} is a hardcoded suggestion, return hint '{}'".format(number, hint))
            return hint

        if arg_name.lower().endswith("tag") and number in level_info["tags"]:
            hint = level_info["tags"][number]
            _debug("resolve_hover_hint - digit {} is a tag, return hint '{}'".format(number, hint))
            return hint

    _debug("resolve_hover_hint - no hint")
    return None


def resolve_completions(cursor_position, buffer_words, function_definitions, shortcuts, level_info, local_functions):
    """
    Given the cursor context and data, returns a (completions, flags) tuple suitable for Sublime's on_query_completions.
    """
    completions = []
    if cursor_position and cursor_position["arg_index"] is not None:
        _debug("resolve_completions - look for function argument completions")
        function_id = cursor_position["function_id"]
        arg_index = cursor_position["arg_index"]

        if function_id in function_definitions:
            arg_name = function_definitions[function_id]["args"][arg_index]
            _debug("resolve_completions - argument name is {}".format(arg_name))

            completions = []
            if arg_name == "eventNumber" and level_info:
                completions = [(name, str(number)) for number, name in level_info["events"].items()]
            
            elif arg_name in _VARIABLE_NAME_TO_DEFINITION_ID and level_info:
                definition_ids = _VARIABLE_NAME_TO_DEFINITION_ID[arg_name]
                tags = [tag for did in definition_ids for tag in level_info["things"].get(did, [])]
                completions = [(level_info["tags"][tag], str(tag)) for tag in tags]

            elif arg_name in _HARDCODED_SUGGESTIONS:
                completions = [(text, value) for value, text in _HARDCODED_SUGGESTIONS[arg_name].items()]

            elif arg_name.lower().endswith("tag") and level_info:
                completions = [(name, str(number)) for number, name in level_info["tags"].items()]

            if completions:
                _debug("resolve_completions - function argument completions found")
                return (completions, sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS)
        else:
            _debug("resolve_completions - function {} is not predefined".format(function_id))
    
    # 2. General completion: Provide functions, shortcuts, and variables from the buffer
    _debug("resolve_completions - providing general suggestions")
    completions = []

    # Functions (with snippet generation)
    for func_id, definition in function_definitions.items():
        name = definition["name"]
        args = definition["args"]
        tags = set(definition.get("tags", []))

        if "control" in tags:
            # Control flow (e.g., If, While) gets a block and no semicolon
            contents = "{}(${{1:condition}})\n{{\n\t${{2:body}}\n}}".format(name)
        else:
            arg_placeholders = ["${{{}:{}}}".format(i+1, arg) for i, arg in enumerate(args)]
            # Predicates (e.g., Equals, Less) get no semicolon
            suffix = "" if "predicate" in tags else ";"
            contents = "{}({}){}".format(name, ", ".join(arg_placeholders), suffix)

        trigger = "{}({})\tfn".format(name, ", ".join(args))
        completions.append((trigger, contents))

    # Shortcuts
    for shortcut in shortcuts:
        trigger = "{}\t{}".format(shortcut["trigger"], shortcut.get("annotation", "snippet"))
        completions.append((trigger, shortcut["contents"]))

    # Buffer variables and Local Functions
    # We combine them to ensure local functions are included even if extract_completions missed them
    all_words = set(buffer_words) | set(local_functions.keys())
    
    for word in all_words:
        # Case-insensitive deduplication check against already added functions/shortcuts
        word_lower = word.lower()
        if any(c[0].split("\t")[0].split("(")[0].lower() == word_lower for c in completions) or \
           any(c[0].split("\t")[0].lower() == word_lower for c in completions):
            continue
        
        if word in local_functions:
            # Buffer word is defined as a function in the current file
            args = local_functions[word]
            arg_placeholders = ["${{{}:{}}}".format(i+1, arg) for i, arg in enumerate(args)]
            contents = "{}({});".format(word, ", ".join(arg_placeholders))
            trigger = "{}({})\tfn".format(word, ", ".join(args))
            completions.append((trigger, contents))
        else:
            # Generic variable from buffer
            completions.append((word + "\tvar", word))

    _debug("resolve_completions - returning {} general suggestions".format(len(completions)))
    return (completions, sublime.INHIBIT_WORD_COMPLETIONS)


class FallenAcesScriptEventListener(sublime_plugin.EventListener):

    def _should_apply(self, view):
        return view.match_selector(0, "source.fallen-aces")

    def on_hover(self, view, point, zone):
        _check_debug_enabled_flag(view)

        if not self._should_apply(view):
            _debug("on_hover - should not apply, return")
            return

        if zone != sublime.HOVER_TEXT:
            _debug("on_hover - zone is {} not HOVER_TEXT, return".format(zone))
            return

        word = view.substr(view.word(point))
        hint = resolve_hover_hint(
            word,
            get_cursor_position(view, point),
            get_function_definitions(),
            get_level_info(view),
        )
        if hint:
            view.show_popup(hint, location=point, flags=sublime.HIDE_ON_MOUSE_MOVE_AWAY, max_width=800)

    def on_query_completions(self, view, prefix, locations):
        _check_debug_enabled_flag(view)
        if not self._should_apply(view):
            _debug("on_query_completions - should not apply, return")
            return

        # Local Function Discovery (from current buffer)
        local_functions = {}
        content = view.substr(sublime.Region(0, view.size()))
        # Match word followed by (args)
        for match in re.finditer(r'\b([a-zA-Z][a-zA-Z0-9_]*)\b\s*\((.*?)\)', content):
            name = match.group(1)
            raw_args = match.group(2)
            # Parse arguments: split by comma, strip whitespace and quotes
            args = []
            if raw_args.strip():
                for arg in raw_args.split(","):
                    clean_arg = arg.strip().strip('"\'')
                    if clean_arg:
                        args.append(clean_arg)
            local_functions[name] = args

        return resolve_completions(
            get_cursor_position(view, locations[0]),
            view.extract_completions(prefix),
            get_function_definitions(),
            get_shortcuts(),
            get_level_info(view),
            local_functions
        )
