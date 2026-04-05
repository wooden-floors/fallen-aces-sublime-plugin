import sublime
import collections

try:
    from ..fa_parser import cursor_parser
    from . import world_data_provider
    from . import definition_provider
    from ..fa_utils import logger
except (ImportError, ValueError):
    from fa_parser import cursor_parser
    from fa_core import world_data_provider
    from fa_core import definition_provider
    from fa_utils import logger

class PhantomManager:
    """
    Manages inline phantom hints for Fallen Aces script files.
    Phantoms display names for tags, events, and other numeric identifiers.
    """
    def __init__(self):
        self.phantom_sets = {} # view_id -> PhantomSet
        self.pending_refreshes = {} # view_id -> refresh_id (for debounce)

    def get_phantom_set(self, view):
        view_id = view.id()
        if view_id not in self.phantom_sets:
            self.phantom_sets[view_id] = sublime.PhantomSet(view, "fallen_aces_hints")
        return self.phantom_sets[view_id]

    def is_enabled(self, view):
        """
        Check if phantoms are enabled for the current view.
        """
        return view.settings().get("fallen_aces_show_phantoms", False)

    def toggle(self, view):
        """
        Toggle phantom hints and persist the choice in the Project settings.
        Immediately refreshes/clears phantoms without locking the view setting.
        """
        enabled = not self.is_enabled(view)
        
        # 1. Persist in Project Data if available
        window = view.window()
        if window:
            data = window.project_data() or {}
            settings = data.get("settings", {})
            settings["fallen_aces_show_phantoms"] = enabled
            data["settings"] = settings
            window.set_project_data(data)
            
        # 2. Immediate feedback: just refresh/clear based on the new state
        if enabled:
            self.refresh(view)
        else:
            self.clear(view)
        return enabled

    def clear(self, view):
        """
        Remove all phantoms from the current view.
        """
        phantom_set = self.get_phantom_set(view)
        phantom_set.update([])

    def refresh(self, view):
        """
        Perform an immediate refresh of phantoms in the view.
        """
        self._do_refresh(view)

    def refresh_debounced(self, view, delay=1000):
        """
        Perform a debounced refresh, suitable for on_modified events.
        """
        if not self.is_enabled(view):
            return

        view_id = view.id()
        
        # Increment refresh_id to invalidate previous pending refreshes
        refresh_id = self.pending_refreshes.get(view_id, 0) + 1
        self.pending_refreshes[view_id] = refresh_id
        
        def delayed_refresh():
            if self.pending_refreshes.get(view_id) == refresh_id:
                self._do_refresh(view)
                
        sublime.set_timeout_async(delayed_refresh, delay)

    def _do_refresh(self, view):
        """
        Actual implementation of phantom generation.
        Parses the view and resolves numeric IDs to names.
        """
        if not self.is_enabled(view):
            return

        logger.log("PhantomManager - refreshing phantoms for view {}".format(view.id()))
        
        # 1. Gather all necessary data
        window = view.window()
        if not window:
            return
        
        project_file = window.project_file_name()
        if not project_file:
            return
            
        world_data = world_data_provider.provider.get_world_data(project_file)
        if not world_data:
            return

        definitions = definition_provider.provider.get_function_definitions()
        hardcoded_suggestions = definition_provider.provider.get_hardcoded_suggestions()

        phantoms = []
        
        # 2. Parse the view content
        # We process line-by-line for efficiency and better error isolation
        for line_region in view.lines(sublime.Region(0, view.size())):
            line_text = view.substr(line_region)
            line_start = line_region.begin()
            
            # Use cursor_parser.tokenize to get structural tokens
            tokens = cursor_parser.tokenize(line_text)
            
            # Identify function calls and their arguments
            candidates = cursor_parser.find_calls(tokens)

            # For each call, check if arguments are numbers and if we have hints for them
            for cand in candidates:
                arg_tokens_list = cursor_parser.split_arguments(tokens[cand["body_idx"]:cand["end_idx"]])
                total_args = len(arg_tokens_list)
                
                func_id = "{}[{}]".format(cand["name"], total_args)
                if func_id not in definitions:
                    # Fallback for empty calls or unknown variants (try [0])
                    func_id = "{}[0]".format(cand["name"])
                    if func_id not in definitions:
                        continue
                
                definition = definitions[func_id]
                for arg_idx, arg_tokens in enumerate(arg_tokens_list):
                    if arg_idx >= len(definition["args"]):
                        break
                    
                    # We only care if the argument is a single word token that is a digit
                    if len(arg_tokens) == 1 and arg_tokens[0].type == "word" and arg_tokens[0].value.isdigit():
                        token = arg_tokens[0]
                        number = int(token.value)
                        arg_name = definition["args"][arg_idx]
                        
                        hint = self._resolve_hint(arg_name, token.value, number, world_data, hardcoded_suggestions)

                        if hint:
                            # Create phantom at the end of the token
                            region = sublime.Region(line_start + token.end, line_start + token.end)
                            # subtle gray color for hint comments
                            content = '<span style="color: #888;"> [{}] </span>'.format(hint)
                            phantoms.append(sublime.Phantom(region, content, sublime.LAYOUT_INLINE))

        # 3. Update the view with new phantoms
        phantom_set = self.get_phantom_set(view)
        phantom_set.update(phantoms)

    def _resolve_hint(self, arg_name, word, number, world_data, hardcoded_suggestions):
        """
        Resolve a numeric ID to a human-readable name using world data and enums.
        """
        # 1. Event Number resolution
        if arg_name == "eventNumber" and number in world_data.events:
            return world_data.events[number].name

        # 2. Tag resolution
        if arg_name.lower().endswith("tag") and number in world_data.tags:
            return world_data.tags[number].name
        
        # 3. Hardcoded Enum resolution (e.g. notificationType)
        if arg_name in hardcoded_suggestions:
            return hardcoded_suggestions[arg_name].get(word)

        return None

# Global manager instance
manager = PhantomManager()
