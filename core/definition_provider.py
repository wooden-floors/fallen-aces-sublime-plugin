# core/definition_provider.py
try:
    from ..utils import logger
    from ..parser import definition_parser
except (ImportError, ValueError):
    from utils import logger
    from parser import definition_parser

class DefinitionProvider:
    """
    Component that provides script definitions and shortcuts.
    Handles lazy-loading and caching, delegating parsing to the parser module.
    """
    def __init__(self):
        self._cache = None
        self._loader = None

    def set_loader(self, loader_func):
        """
        Injects the function used to retrieve raw data from the file system.
        """
        self._loader = loader_func

    def _ensure_initialized(self):
        """
        Internal check to load data from the injected loader if the cache is empty.
        """
        if self._cache is not None:
            return

        if not self._loader:
            logger.log("DefinitionProvider - no loader set, initializing empty")
            self._cache = {"functions": {}, "shortcuts": []}
            return

        logger.log("DefinitionProvider - lazy-loading definitions via injected loader")
        raw_data = self._loader()
        self._cache = definition_parser.parse_definitions(raw_data)

    def get_function_definitions(self):
        self._ensure_initialized()
        return self._cache.get("functions", {})

    def get_shortcuts(self):
        self._ensure_initialized()
        return self._cache.get("shortcuts", [])

    def get_variable_to_definition_id(self):
        self._ensure_initialized()
        return self._cache.get("variable_to_definition_id", {})

    def get_hardcoded_suggestions(self):
        self._ensure_initialized()
        return self._cache.get("hardcoded_suggestions", {})

    def clear_cache(self):
        self._cache = None


# Singleton instance provided by the module
provider = DefinitionProvider()
