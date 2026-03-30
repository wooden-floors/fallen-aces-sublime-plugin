# parser/local_function_parser.py
import re

try:
    import sublime
except ImportError:
    sublime = None

# Simple fallback for environments without the Sublime API (like unit tests)
class RegionStub:
    def __init__(self, a, b):
        self.a = a
        self.b = b
    def begin(self): return min(self.a, self.b)
    def end(self): return max(self.a, self.b)

def get_region_class():
    if sublime and hasattr(sublime, "Region"):
        return sublime.Region
    return RegionStub

# Regex to match function name and its argument block
RE_LOCAL_FUNC = re.compile(r'\b([a-zA-Z][a-zA-Z0-9_]*)\b\s*\((.*?)\)')

def discover_local_functions(view):
    """
    Scans the given Sublime view for function definitions and extracts 
    their names and argument lists.
    """
    local_functions = {}
    Region = get_region_class()
    
    # entity.name.function is provided by the sublime-syntax file
    func_regions = view.find_by_selector("entity.name.function.fallen-aces")
    
    for region in func_regions:
        name = view.substr(region)
        
        # Look ahead for the arguments: "FuncName(arg1, arg2)"
        search_end = min(region.end() + 256, view.size())
        lookahead_region = Region(region.end(), search_end)
            
        remainder = view.substr(lookahead_region)
        
        # Combine name and remainder to match the full signature
        full_text = name + remainder
        arg_match = RE_LOCAL_FUNC.search(full_text)
        
        args = []
        if arg_match and arg_match.group(1) == name:
            raw_args = arg_match.group(2)
            if raw_args.strip():
                args = [a.strip().strip('"\'') for a in raw_args.split(",") if a.strip()]
        
        local_functions[name] = args
        
    return local_functions
