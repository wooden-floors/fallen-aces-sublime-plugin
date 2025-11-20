import sublime
import sublime_plugin
import os
import re
import html
import json
 
from .fallen_aces_level_info import get_level_info
from .fallen_aces_function_definition import get_function_definition
from .fallen_aces_cursor import get_cursor_position

VARIABLE_NAME_TO_DEFINITION_ID = {
    "lightStateTag": [517], # LightState
    "lightSourceTag": [518], # PointLight
    "movableGeometryTag": [534], # MovableGeometry
    "moveStateTag": [521], # MoveState
    "enemyTag": [
        10001, # Goon
        10002, # Pipeguy
        10003, # PistolGuy
        10004, # Malone
        10005, # GoonThug
        10006, # PipeguyWiseguy
        10009, # MolotovMook
        10011, # SnipingMook
        10012, # ArmedMook
        10014, # KnifeGuy
        10017, # MachineGunMook
        10021, # BigPalooka
    ]
}

HARDCODED_SUGGESTIONS = {
    "disturbanceTypeName": {
        "SomethingTurnedOn": "SomethingTurnedOn",
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
            elif arg_name in HARDCODED_SUGGESTIONS:
                return HARDCODED_SUGGESTIONS[arg_name][str(word)]
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

        completions = []
        if arg_name == "eventNumber":
            completions = [(name, str(number)) for number, name in level_info["events"].items()]
        elif arg_name in VARIABLE_NAME_TO_DEFINITION_ID:
            definition_ids = VARIABLE_NAME_TO_DEFINITION_ID[arg_name]
            tags = [tag for definition_id in definition_ids for tag in level_info["things"].get(definition_id, [])]
            completions = [(level_info["tags"][tag], str(tag)) for tag in tags]
        elif arg_name in HARDCODED_SUGGESTIONS:
            completions = [(text, value) for value, text in HARDCODED_SUGGESTIONS[arg_name].items()]
        elif arg_name.lower().endswith("tag"):
            completions = [(name, str(number)) for number, name in level_info["tags"].items()]

        if completions:
            return (completions, sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS)

        return None
