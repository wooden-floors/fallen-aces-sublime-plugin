import sublime
import sublime_plugin
import os
import re
import html
import json

from .fallen_aces_level_info import get_level_info
from .fallen_aces_function_definition import get_function_definition
from .fallen_aces_cursor import get_cursor_position

class FallenAcesScriptEventListener(sublime_plugin.EventListener):
    def _should_apply(self, view):
        return view.match_selector(0, "source.fallen-aces")

    def on_hover(self, view, point, zone):
        if not self._should_apply(view):
            return
        if zone != sublime.HOVER_TEXT:
            return

        word = view.substr(view.word(point))
        hint = self._get_hover_hint(view, point, word)

        if hint:
            view.show_popup(
                hint,
                flags=sublime.HIDE_ON_MOUSE_MOVE_AWAY,
                max_width=800
            )
            return True
 
    def _get_hover_hint(self, view, point, word):
        function_definitions = get_function_definition(view)

        if word in function_definitions:
            return function_definitions[word]["hint"]

        if word.isdigit():
            level_info = get_level_info(view)
            word = int(word)

            cursor_position = get_cursor_position(view, point)
            function_name = cursor_position["function_name"]
            arg_index = cursor_position["arg_index"]
            arg_name = function_definitions[function_name]["args"][arg_index]

            if arg_name == "eventNumber" and word in level_info["events"]:
                 return level_info["events"][word]
            elif arg_name.lower().endswith("tag") and word in level_info["tags"]:
                return level_info["tags"][word]

        return None
      
    def on_query_completions(self, view, prefix, locations):
        if not self._should_apply(view):
            return

        cursor_position = get_cursor_position(view, locations[0])
        if not cursor_position:
            return

        function_name = cursor_position["function_name"]
        arg_index = cursor_position["arg_index"]

        function_definitions = get_function_definition(view)

        arg_name = function_definitions[function_name]["args"][arg_index]

        level_info = get_level_info(view)
        if arg_name == "eventNumber":
            completions = [(name, str(number)) for number, name in level_info["events"].items()]
            return (completions, sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS)
        elif arg_name.lower().endswith("tag"):
            completions = [(name, str(number)) for number, name in level_info["tags"].items()]
            return (completions, sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS)
        return None