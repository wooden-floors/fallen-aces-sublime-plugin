# core/resolver.py
import collections

try:
    from ..fa_utils import logger
    from ..fa_utils.formatter import format_hint_html
except (ImportError, ValueError):
    from fa_utils import logger
    from fa_utils.formatter import format_hint_html

# HoverContext encapsulates data needed to resolve a hover hint.
HoverContext = collections.namedtuple("HoverContext", [
    "cursor",           # Result of cursor_parser.parse_cursor_position
    "world_data",       # Result of world_data_provider.get_world_data
    "definitions",      # Dict of function definitions
    "hardcoded_suggestions" # Dict of hardcoded enum-like values
])

# CompletionContext encapsulates data needed to resolve autocompletions.
CompletionContext = collections.namedtuple("CompletionContext", [
    "cursor",           # Result of cursor_parser.parse_cursor_position
    "world_data",       # Result of world_data_provider.get_world_data
    "definitions",      # Dict of function definitions
    "shortcuts",        # List of static shortcuts
    "local_functions",  # Dict of functions in current file
    "buffer_words",     # List of words in current view
    "variable_to_definition_id", # Maps arg names to world IDs
    "hardcoded_suggestions" # Dict of hardcoded enum-like values
])

# --- Resolver Logic ---

def resolve_hover_hint(word, context):
    """
    Given the hovered word and context, returns an HTML hint string or None.
    """
    if not context.cursor:
        logger.log("Resolver - empty cursor, return")
        return None

    function_id = context.cursor["function_id"]
    function_name = context.cursor["function_name"]

    # 1. Check if hovering on a function name
    if function_name == word and function_id in context.definitions:
        logger.log("Resolver - hover on function name, return hint")
        return format_hint_html(context.definitions[function_id])

    # 2. Check if hovering on a digit (argument value)
    if word.isdigit():
        logger.log("Resolver - hover on a digit")

        if not context.world_data:
            logger.log("Resolver - world data is missing, return")
            return None

        arg_index = context.cursor["arg_index"]
        if arg_index is None:
            logger.log("Resolver - digit is not a function argument, return")
            return None

        if function_id not in context.definitions:
            logger.log("Resolver - digit is an argument for unknown function, return")
            return None

        arg_name = context.definitions[function_id]["args"][arg_index]
        number = int(word)

        logger.log("Resolver - digit {} is an argument {} of function {}".format(number, arg_name, function_id))

        # Event Number resolution
        if arg_name == "eventNumber" and number in context.world_data.events:
            event = context.world_data.events[number]
            hint = "{} - {}".format(event.name, event.number)
            logger.log("Resolver - return event hint '{}'".format(hint))
            return hint

        # Hardcoded Enum resolution
        if arg_name in context.hardcoded_suggestions:
            hint = context.hardcoded_suggestions[arg_name].get(word)
            logger.log("Resolver - return hardcoded hint '{}'".format(hint))
            return hint

        # Tag resolution
        if arg_name.lower().endswith("tag") and number in context.world_data.tags:
            tag = context.world_data.tags[number]
            hint = "{} - {}".format(tag.name, tag.number)
            logger.log("Resolver - return tag hint '{}'".format(hint))
            return hint

    logger.log("Resolver - no hint found")
    return None


def resolve_completions(context):
    """
    Given the context, returns a list of completions.
    """
    # 1. Specialized Argument Completion
    if context.cursor and context.cursor["arg_index"] is not None:
        logger.log("Resolver - look for function argument completions")
        function_id = context.cursor["function_id"]
        arg_index = context.cursor["arg_index"]

        if function_id in context.definitions:
            arg_name = context.definitions[function_id]["args"][arg_index]
            logger.log("Resolver - argument name is {}".format(arg_name))
            completions = []

            if arg_name == "eventNumber" and context.world_data:
                completions = [("{} - {}".format(e.name, e.number), str(n)) for n, e in context.world_data.events.items()]
            
            elif arg_name in context.variable_to_definition_id and context.world_data:
                mapping = context.variable_to_definition_id[arg_name]
                definition_ids = [int(did) for did in mapping.keys()]
                tags_ids = [tag_id for did in definition_ids for tag_id in context.world_data.things.get(did, [])]
                completions = [("{} - {}".format(context.world_data.tags[tid].name, tid), str(tid)) for tid in tags_ids if tid in context.world_data.tags]

            elif arg_name in context.hardcoded_suggestions:
                completions = [(text, value) for value, text in context.hardcoded_suggestions[arg_name].items()]

            elif arg_name.lower().endswith("tag") and context.world_data:
                completions = [("{} - {}".format(t.name, t.number), str(n)) for n, t in context.world_data.tags.items()]

            if completions:
                logger.log("Resolver - specialized argument completions found")
                return completions
        else:
            logger.log("Resolver - function {} is not predefined".format(function_id))
    
    # 2. General Global Completion
    logger.log("Resolver - providing general suggestions")
    completions = []

    # Predefined Functions
    for func_id, definition in context.definitions.items():
        name = definition["name"]
        args = definition["args"]
        tags = set(definition.get("tags", []))

        if "control" in tags:
            contents = "{}(${{1:condition}})\n{{\n\t${{2:body}}\n}}".format(name)
        else:
            arg_placeholders = ["${{{}:{}}}".format(i+1, arg) for i, arg in enumerate(args)]
            suffix = "" if "predicate" in tags else ";"
            contents = "{}({}){}".format(name, ", ".join(arg_placeholders), suffix)

        trigger = "{}({})\tfn".format(name, ", ".join(args))
        completions.append((trigger, contents))

    # Static Shortcuts
    for shortcut in context.shortcuts:
        trigger = "{}\t{}".format(shortcut["trigger"], shortcut.get("annotation", "snippet"))
        completions.append((trigger, shortcut["contents"]))

    # Buffer words and Local Functions
    all_words = set(context.buffer_words) | set(context.local_functions.keys())
    for word in all_words:
        word_lower = word.lower()
        if any(c[0].split("\t")[0].split("(")[0].lower() == word_lower for c in completions) or \
           any(c[0].split("\t")[0].lower() == word_lower for c in completions):
            continue
        
        if word in context.local_functions:
            args = context.local_functions[word]
            arg_placeholders = ["${{{}:{}}}".format(i+1, arg) for i, arg in enumerate(args)]
            contents = "{}({});".format(word, ", ".join(arg_placeholders))
            trigger = "{}({})\tfn".format(word, ", ".join(args))
            completions.append((trigger, contents))
        else:
            completions.append((word + "\tvar", word))

    logger.log("Resolver - returning {} general suggestions".format(len(completions)))
    return completions
