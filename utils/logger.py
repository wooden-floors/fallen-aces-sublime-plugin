# utils/logger.py
_ENABLED = False

def set_enabled(val):
    global _ENABLED
    _ENABLED = val

def log(msg):
    if _ENABLED:
        print("[FallenAcesPlugin]: {}".format(msg))
