# fa_parser/definition_parser.py
import json
import collections

try:
    from ..fa_utils import logger
except (ImportError, ValueError):
    from fa_utils import logger

# Data structures for script definitions
# FunctionVariant represents a specific overload of a function
FunctionVariant = collections.namedtuple("FunctionVariant", 
    ["name", "args", "description", "usage", "tags"])

def parse_definitions(raw_data):
    """
    Parses raw JSON data into a structured definition dictionary.
    Returns a default empty structure if parsing fails.
    """
    default_state = {"functions": {}, "shortcuts": []}

    if not raw_data:
        return default_state

    try:
        json_data = json.loads(raw_data)
    except Exception as e:
        logger.log("parse_definitions - error parsing JSON: {}".format(e))
        return default_state

    functions = {}
    for func_data in json_data.get("functions", []):
        name = func_data["name"]
        tags = func_data.get("tags", [])
        for variant_data in func_data.get("variants", []):
            args = variant_data.get("args", [])
            # ID format: Name[ArgCount] (e.g., SetState[2])
            func_id = "{}[{}]".format(name, len(args))
            
            # We currently return a dict for compatibility with UI helpers
            functions[func_id] = {
                "name": name,
                "args": args,
                "description": variant_data.get("description"),
                "usage": variant_data.get("usage"),
                "tags": tags
            }

    parsed = {
        "functions": functions,
        "shortcuts": json_data.get("shortcuts", []),
        "variable_to_definition_id": json_data.get("variable_to_definition_id", {}),
        "hardcoded_suggestions": json_data.get("hardcoded_suggestions", {})
    }
    
    logger.log("parse_definitions - parsed {} functions and {} shortcuts".format(
        len(parsed["functions"]), len(parsed["shortcuts"])))

    return parsed
