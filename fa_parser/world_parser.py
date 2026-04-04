import re
from collections import namedtuple

try:
    from ..fa_utils import logger
except (ImportError, ValueError):
    from fa_utils import logger

# --- Data Structures ---

Event = namedtuple("Event", ["name", "number"])
Tag = namedtuple("Tag", ["name", "number"])
Thing = namedtuple("Thing", ["definition_id", "tag"])

class WorldData:
    """
    Container for parsed world file data.
    """
    def __init__(self, events, tags, things):
        self.events = events  # {number: Event}
        self.tags = tags      # {number: Tag}
        self.things = things  # {definition_id: [tag, ...]}


# --- fa_parser Logic ---

RE_BLOCKS = {
    "event": re.compile(r'Event\s*\{(.*?)\}', re.DOTALL),
    "tag":   re.compile(r'Tag\s*\{(.*?)\}', re.DOTALL),
    "thing": re.compile(r'Thing\b[^\{]*\{(.*?)\}', re.DOTALL),
}

RE_FIELDS = {
    "name":          re.compile(r'name\s*=\s*"(.*?)"'),
    "number":        re.compile(r'number\s*=\s*(\d+)'),
    "definition_id": re.compile(r'definition_id\s*=\s*(\d+)'),
    "tag":           re.compile(r'tag\s*=\s*(\d+)'),
}

def parse_world_file(raw):
    """
    Parses the contents of a world file and returns a WorldData object.
    """
    if not raw:
        logger.log("parse_world_file - empty input, return")
        return None

    events = {}
    for block in RE_BLOCKS["event"].findall(raw):
        name = _extract_field(block, "name")
        num = _extract_field(block, "number", int)
        if name and num is not None:
            events[num] = Event(name, num)

    tags = {}
    for block in RE_BLOCKS["tag"].findall(raw):
        name = _extract_field(block, "name")
        num = _extract_field(block, "number", int)
        if name and num is not None:
            tags[num] = Tag(name, num)

    things = {}
    for block in RE_BLOCKS["thing"].findall(raw):
        definition_id = _extract_field(block, "definition_id", int)
        tag = _extract_field(block, "tag", int)
        if definition_id is not None and tag is not None:
            things.setdefault(definition_id, []).append(tag)

    result = WorldData(events, tags, things)
    logger.log("parse_world_file - parsed {} events, {} tags, {} things".format(
        len(events), len(tags), len(things)
    ))
    return result


def _extract_field(block, field_name, transform=None):
    """
    Extract specific field from a block using pre-compiled regex.
    """
    match = RE_FIELDS[field_name].search(block)
    if not match:
        return None
    
    val = match.group(1)
    return transform(val) if transform else val
