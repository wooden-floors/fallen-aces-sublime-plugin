import sublime
import sublime_plugin
import os

try:
    from .fa_utils import logger
    from .fa_utils.formatter import format_hint_html
    from .fa_parser import cursor_parser
    from .fa_parser import world_parser
    from .fa_parser import local_function_parser
    from .fa_core import definition_provider
    from .fa_core import world_data_provider
    from .fa_core import resolver
    from .fa_core import phantom_manager
except (ImportError, ValueError):
    from fa_utils import logger
    from fa_utils.formatter import format_hint_html
    from fa_parser import cursor_parser
    from fa_parser import world_parser
    from fa_parser import local_function_parser
    from fa_core import definition_provider
    from fa_core import world_data_provider
    from fa_core import resolver
    from fa_core import phantom_manager

# Dynamically detect our package name (handles renames and zipped packages)
PACKAGE_NAME = os.path.basename(os.path.dirname(__file__)).replace(".sublime-package", "")

# ---------------------------------------------------------------------------
# Definition Provider Setup
# ---------------------------------------------------------------------------

def load_plugin_resource(file_name):
    """
    Reads a file from the plugin folder using Sublime API.
    Handles zipped packages, renames, and resource overrides automatically.
    """
    resource_path = "Packages/{}/{}".format(PACKAGE_NAME, file_name)
    try:
        return sublime.load_resource(resource_path)
    except Exception:
        logger.log("load_plugin_resource - resource {} not found at {}".format(file_name, resource_path))
        return None

# Tell the definitions provider how to load its data
definition_provider.provider.set_loader(lambda: load_plugin_resource("fallen-aces-data.json"))

# ---------------------------------------------------------------------------
# Logging & Settings
# ---------------------------------------------------------------------------

def _sync_logger_settings(view):
    """
    Syncs the global logger state with the current view's settings.
    """
    enabled = view.settings().get("fallen_aces_plugin_debug_enabled", False)
    logger.set_enabled(enabled)


# ---------------------------------------------------------------------------
# Context Helpers
# ---------------------------------------------------------------------------

def create_hover_context(view, point):
    """
    Gathers only the data necessary for resolving a hover hint.
    """
    return resolver.HoverContext(
        cursor=get_cursor_position(view, point),
        world_data=get_world_data(view),
        definitions=definition_provider.provider.get_function_definitions(),
        hardcoded_suggestions=definition_provider.provider.get_hardcoded_suggestions()
    )


def create_completion_context(view, point, prefix):
    """
    Gathers all data necessary for resolving autocompletions.
    """
    return resolver.CompletionContext(
        cursor=get_cursor_position(view, point),
        world_data=get_world_data(view),
        definitions=definition_provider.provider.get_function_definitions(),
        shortcuts=definition_provider.provider.get_shortcuts(),
        local_functions=local_function_parser.discover_local_functions(view),
        buffer_words=view.extract_completions(prefix),
        buffer_strings=local_function_parser.discover_buffer_strings(view),
        variable_to_definition_id=definition_provider.provider.get_variable_to_definition_id(),
        hardcoded_suggestions=definition_provider.provider.get_hardcoded_suggestions()
    )


def get_cursor_position(view, point):
    """
    Retrieves the logical cursor context.
    """
    line_region = view.line(point)
    line = view.substr(line_region)
    cursor_offset = point - line_region.begin()
    return cursor_parser.parse_cursor_position(line, cursor_offset)


def get_world_data(view):
    """
    Retrieves the parsed world data (tags, events) for the current project.
    """
    window = view.window()
    if not window:
        logger.log("get_world_data - no window, return")
        return None

    project_file = window.project_file_name()
    if not project_file:
        logger.log("get_world_data - no project file, return")
        return None

    return world_data_provider.provider.get_world_data(project_file)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def _toggle_project_setting(window, setting_key, label):
    """
    Helper to toggle a boolean setting in the current .sublime-project file.
    """
    project_data = window.project_data()
    if project_data is None:
        sublime.error_message("Fallen Aces: No project open. Project settings are required to toggle '{}'.".format(setting_key))
        return None

    settings = project_data.get("settings", {})
    current = settings.get(setting_key, False)
    new_state = not current
    settings[setting_key] = new_state
    project_data["settings"] = settings
    window.set_project_data(project_data)

    status = "Enabled" if new_state else "Disabled"
    sublime.status_message("Fallen Aces {}: {}".format(label, status))
    return new_state


class FallenAcesTogglePhantomsCommand(sublime_plugin.TextCommand):
    """
    Command to toggle inline phantom hints for tags and events.
    """
    def run(self, edit):
        enabled = phantom_manager.manager.toggle(self.view)
        sublime.status_message("Fallen Aces Phantoms: {}".format("Enabled" if enabled else "Disabled"))

    def is_visible(self):
        return self.view.match_selector(0, "source.fallen-aces")


class FallenAcesToggleAutoSyntaxCommand(sublime_plugin.WindowCommand):
    """
    Command to toggle automatic syntax application for .txt files in 'scripts' folders.
    """
    def run(self):
        _toggle_project_setting(self.window, "fallen_aces_auto_syntax_enabled", "Auto Syntax")


class FallenAcesToggleDebugLoggingCommand(sublime_plugin.WindowCommand):
    """
    Command to toggle debug logging for the plugin.
    """
    def run(self):
        new_state = _toggle_project_setting(self.window, "fallen_aces_plugin_debug_enabled", "Debug Logging")
        if new_state is not None:
            logger.set_enabled(new_state)


# ---------------------------------------------------------------------------
# Event Listener
# ---------------------------------------------------------------------------

class FallenAcesScriptEventListener(sublime_plugin.EventListener):
    """
    Main entry point for Sublime Text events. 
    Coordinates between the editor and the plugin's core logic.
    """

    def _should_apply(self, view):
        """
        Checks if the plugin logic should run for the current view.
        """
        return view.match_selector(0, "source.fallen-aces")

    def _check_and_apply_syntax(self, view):
        """
        Automatically applies Fallen Aces syntax to .txt files inside 'scripts' 
        folders if the feature is enabled in settings.
        """
        if not view.settings().get("fallen_aces_auto_syntax_enabled", False):
            return

        file_path = view.file_name()
        if not file_path or not file_path.lower().endswith(".txt"):
            return

        # Check if the file is in a folder named 'scripts'
        parent_folder = os.path.basename(os.path.dirname(file_path)).lower()
        if parent_folder == "scripts":
            syntax_path = "Packages/{}/fallen-aces.sublime-syntax".format(PACKAGE_NAME)
            if view.settings().get("syntax") != syntax_path:
                logger.log("Auto-applying syntax to: {}".format(file_path))
                view.set_syntax_file(syntax_path)

    def on_load(self, view):
        self._check_and_apply_syntax(view)
        if self._should_apply(view):
            phantom_manager.manager.refresh(view)

    def on_post_save(self, view):
        self._check_and_apply_syntax(view)
        if self._should_apply(view):
            phantom_manager.manager.refresh(view)

    def on_activated(self, view):
        if self._should_apply(view):
            phantom_manager.manager.refresh(view)

    def on_modified_async(self, view):
        if self._should_apply(view):
            phantom_manager.manager.refresh_debounced(view)

    def on_hover(self, view, point, zone):
        """
        Triggered when the user hovers over text. Resolves and displays hover hints.
        """
        _sync_logger_settings(view)

        if not self._should_apply(view):
            logger.log("on_hover - should not apply, return")
            return

        if zone != sublime.HOVER_TEXT:
            logger.log("on_hover - zone is {} not HOVER_TEXT, return".format(zone))
            return

        word = view.substr(view.word(point))
        context = create_hover_context(view, point)
        hint = resolver.resolve_hover_hint(word, context)
        
        if hint:
            view.show_popup(hint, location=point, flags=sublime.HIDE_ON_MOUSE_MOVE_AWAY, max_width=800)

    def on_query_completions(self, view, prefix, locations):
        """
        Triggered when the user requests autocompletions.
        """
        _sync_logger_settings(view)
        if not self._should_apply(view):
            logger.log("on_query_completions - should not apply, return")
            return

        context = create_completion_context(view, locations[0], prefix)
        completions = resolver.resolve_completions(context)

        return (completions, sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS)
