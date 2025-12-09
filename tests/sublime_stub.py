import sys
import types

sublime_stub = types.ModuleType("sublime")
sublime_stub.packages_path = lambda: "/stub/packages"
sublime_stub.HOVER_TEXT = 1
sublime_stub.INHIBIT_WORD_COMPLETIONS = 1
sublime_stub.INHIBIT_EXPLICIT_COMPLETIONS = 2
sys.modules["sublime"] = sublime_stub

sublime_plugin_stub = types.ModuleType("sublime_plugin")
sublime_plugin_stub.EventListener = object
sys.modules["sublime_plugin"] = sublime_plugin_stub