import sys
import types

class RegionStub:
    def __init__(self, a, b):
        self.a = a
        self.b = b
    def begin(self): return min(self.a, self.b)
    def end(self): return max(self.a, self.b)

sublime_stub = types.ModuleType("sublime")
sublime_stub.packages_path = lambda: "/stub/packages"
sublime_stub.HOVER_TEXT = 1
sublime_stub.INHIBIT_WORD_COMPLETIONS = 1
sublime_stub.INHIBIT_EXPLICIT_COMPLETIONS = 2
sublime_stub.LAYOUT_INLINE = 0
sublime_stub.PhantomSet = lambda *args: None
sublime_stub.Phantom = lambda *args: None
sublime_stub.Region = RegionStub
sublime_stub.set_timeout_async = lambda c, d: None
sublime_stub.status_message = lambda m: None
sublime_stub.error_message = lambda m: None
sys.modules["sublime"] = sublime_stub

sublime_plugin_stub = types.ModuleType("sublime_plugin")
sublime_plugin_stub.EventListener = object

class TextCommandStub:
    def __init__(self, view):
        self.view = view
sublime_plugin_stub.TextCommand = TextCommandStub

class WindowCommandStub:
    def __init__(self, window):
        self.window = window
sublime_plugin_stub.WindowCommand = WindowCommandStub

sys.modules["sublime_plugin"] = sublime_plugin_stub