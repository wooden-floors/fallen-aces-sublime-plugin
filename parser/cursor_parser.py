# parser/cursor_parser.py
import collections

try:
    from ..utils import logger
except (ImportError, ValueError):
    from utils import logger

# Token representation for clearer structural analysis
Token = collections.namedtuple("Token", ["type", "value", "start", "end"])

def tokenize(line):
    """
    Splits a line of code into structural tokens: words, strings, comments, 
    and punctuation (parens, commas).
    """
    tokens = []
    i = 0
    line_len = len(line)
    
    while i < line_len:
        char = line[i]
        
        # 1. Comments (//)
        if char == '/' and i + 1 < line_len and line[i+1] == '/':
            tokens.append(Token("comment", line[i:], i, line_len))
            break
            
        # 2. Strings (" or ') with escape support
        if char in ('"', "'"):
            quote_char = char
            start = i
            i += 1
            while i < line_len:
                if line[i] == '\\' and i + 1 < line_len:
                    i += 2 # Skip escaped character
                    continue
                if line[i] == quote_char:
                    i += 1
                    break
                i += 1
            tokens.append(Token("string", line[start:i], start, i))
            continue
            
        # 3. Structural characters
        if char in ('(', ')', ','):
            tokens.append(Token(char, char, i, i + 1))
            i += 1
            continue
            
        # 4. Words (function names, variable names)
        if char.isalnum() or char == '_':
            start = i
            while i < line_len and (line[i].isalnum() or line[i] == '_'):
                i += 1
            tokens.append(Token("word", line[start:i], start, i))
            continue
            
        i += 1
    return tokens

def parse_cursor_position(line, cursor_offset):
    """
    Identifies which function call the cursor is inside and which argument index 
    it is pointing to. Handles nested calls and complex strings.
    """
    logger.log("parse_cursor_position - line='{}', cursor_offset={}".format(line, cursor_offset))

    tokens = tokenize(line)
    
    # 1. Identify all valid function call candidates (word followed by '(')
    candidates = []
    for idx, token in enumerate(tokens):
        if token.type == "word" and idx + 1 < len(tokens) and tokens[idx+1].type == "(":
            name = token.value
            start = token.start
            args_start = tokens[idx+1].end
            
            # Find matching ')' by tracking the nesting stack
            stack = 1
            end = -1
            for j in range(idx + 2, len(tokens)):
                t = tokens[j]
                if t.type == "(":
                    stack += 1
                elif t.type == ")":
                    stack -= 1
                    if stack == 0:
                        end = t.start
                        break
                elif t.type == "comment":
                    break
            
            if end != -1:
                candidates.append({
                    "name": name,
                    "start": start,
                    "args_start": args_start,
                    "end": end,
                    "body_idx": idx + 2 # Where arguments begin
                })

    # 2. Find the innermost function containing the cursor
    active = None
    for cand in candidates:
        if cand["start"] < cursor_offset <= cand["end"]:
            if active is None or cand["start"] > active["start"]:
                active = cand

    if not active:
        logger.log("parse_cursor_position - no active function at cursor")
        return None

    # 3. Calculate argument metadata (total count and current index)
    total_args = 0
    arg_index = 0
    has_content = False
    stack = 0
    found_cursor = False
    
    # The cursor is "on the name" if it is at or before the opening '('
    is_on_name = cursor_offset <= active["args_start"]
    
    for j in range(active["body_idx"], len(tokens)):
        t = tokens[j]
        # Stop at the end of the active function
        if t.start >= active["end"]:
            break
            
        if not found_cursor and t.start >= cursor_offset:
            found_cursor = True
            
        if t.type == "(":
            stack += 1
        elif t.type == ")":
            stack -= 1
        elif t.type == "," and stack == 0:
            total_args += 1
            if not found_cursor:
                arg_index += 1
        elif stack == 0 and t.type != "comment":
            # Any non-punctuation token at top level means we have at least one arg
            has_content = True
            
    if has_content:
        total_args += 1
        
    result = {
        "function_id": "{}[{}]".format(active["name"], total_args),
        "function_name": active["name"],
        "arg_index": None if is_on_name else arg_index,
    }
    
    logger.log("parse_cursor_position - result={}".format(result))
    return result
