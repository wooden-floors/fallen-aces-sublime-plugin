import sublime
import sublime_plugin
import os
import re
import html
import json

CACHE = {}
DEBUG_ENABLED = False

def _log(msg):
    if DEBUG_ENABLED:
        print('[FUNCTION DEFINITION]: {}'.format(msg))

def get_function_definition(view):
    global DEBUG_ENABLED
    DEBUG_ENABLED = view.settings().get("fallen_aces_plugin_debug_enabled")

    if CACHE:
        _log("Get cached function definition")
        return CACHE

    _log("Read parse function definition")

    args = _parse_function_args()
    hints = _parse_function_hints()

    for function_name in args.keys():
        CACHE[function_name] = {
            "args": args[function_name],
            "hint": hints.get(function_name)
        }

    return CACHE

def _parse_function_hints():
    packages_path = sublime.packages_path()
    path = os.path.join(packages_path, "User", "fallen-aces.md")

    if not os.path.exists(path):
        return {}

    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    function_hints = {}
    sections = re.split(r'\n(?=## )', text)
    for section in sections:
        lines = section.strip().splitlines()
        if not lines:
            continue

        function_line = lines[0].lstrip("# ").strip()
        function_name = function_line.split("(")[0]

        function_hints[function_name] = _parse_markdown_to_html(section)

    return function_hints

def _parse_markdown_to_html(text):
    text = re.sub(r'^## (.*)$', r'<b>\1</b><br>', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*(.*?)\*\*', r'<br><br><b>\1</b><br>', text)
    text = re.sub(
        r'```([^`\n]*)\n(.*?)```',
        lambda m: '''
    <div style="
        background-color:#272822;
        color:#f8f8f2;
        padding:5px;
        border-radius:4px;
    ">
    {}
    </div>
    '''.format("<br>".join(html.escape(m.group(2)).splitlines())),
        text,
        flags=re.DOTALL
    )

    return text

def _parse_function_args():
    packages_path = sublime.packages_path()
    path = os.path.join(packages_path, "User", "fallen-aces.sublime-completions")

    if not os.path.exists(path):
        return {}

    with open(path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    raw_text = re.sub(r'^\s*//.*$', '', raw_text, flags=re.MULTILINE)
    data = json.loads(raw_text)

    function_args = {}

    for completion in data.get("completions", []):
        function_name = completion.get("trigger")
        function_args[function_name] = re.findall(r'\$\{\d+:([^}]+)\}', completion.get("contents"))

    # _log(function_definitions)
    return function_args
