import sublime
import sublime_plugin
import os
import re
import html
import json

def _log(msg):
    if DEBUG_ENABLED:
        print("[CURSOR]: {}".format(msg))
      
def get_cursor_position(view, point):
    global DEBUG_ENABLED 
    DEBUG_ENABLED = view.settings().get("fallen_aces_plugin_debug_enabled")

    line_region = view.line(point)
    line = view.substr(line_region)

    cursor_in_line = point - line_region.begin()

    match = re.search(r'(\w+)\s*\(([^)]*)\)', line)
    if not match:
        return

    func_name = match.group(1)
    args_text = match.group(2)
    args_start = match.start(2)

    _log("Function name {}".format(func_name))
    _log("Args {}".format(args_text))

    args = []
    for match_arg in re.finditer(r'([^,]+)', args_text):
        start = match_arg.start(1)
        end = match_arg.end(1)
        cleaned = match_arg.group(1).strip()
        args.append((start, end, cleaned))

    arg_index = None
    for i, (start, end, cleaned) in enumerate(args):
        abs_start = args_start + start
        abs_end = args_start + end
        if abs_start <= cursor_in_line <= abs_end:
            arg_index = i
            break

    if arg_index is None:
        return None

    return {
        "function_name": func_name,
        "arg_index": arg_index
    }