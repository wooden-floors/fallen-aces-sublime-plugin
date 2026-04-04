# core/world_data_provider.py
import os
try:
    from ..fa_utils import logger
    from ..fa_parser import world_parser
    from ..fa_parser import chapter_info_parser
except (ImportError, ValueError):
    from fa_utils import logger
    from fa_parser import world_parser
    from fa_parser import chapter_info_parser

class WorldDataProvider:
    """
    Component that provides world data (tags, events, things) for Fallen Aces projects.
    Handles multi-project caching and file modification tracking.
    """
    def __init__(self):
        # { project_file_path: { cache_metadata } }
        self._project_cache = {}

    def get_world_data(self, project_file):
        """
        Returns world data for given project. 
        Returns None if expected files are missing or parsing fails.
        """
        if not project_file:
            return None

        if project_file not in self._project_cache:
            logger.log("WorldDataProvider - project file is not in cache: {}".format(project_file))
            
            folder = os.path.dirname(project_file)
            chapter_info_path = os.path.join(folder, "chapterInfo.txt")

            if not os.path.exists(chapter_info_path):
                logger.log("WorldDataProvider - chapterInfo.txt not found in {}".format(folder))
                return None
            
            self._project_cache[project_file] = {
                "chapterInfoPath": chapter_info_path,
                "chapterInfoLastReloadTime": None,
                "worldFilePath": None,
                "worldFileLastReloadTime": None,
                "worldData": None
            }

        cache = self._project_cache[project_file]
        chapter_info_path = cache["chapterInfoPath"]
        
        # 1. Check if chapterInfo.txt changed (might point to a different world file)
        chapter_info_mtime = os.path.getmtime(chapter_info_path)
        if cache["chapterInfoLastReloadTime"] is None or cache["chapterInfoLastReloadTime"] < chapter_info_mtime:
            logger.log("WorldDataProvider - reload world file path from chapterInfo.txt")
            cache["worldFilePath"] = chapter_info_parser.get_world_file_path(chapter_info_path)
            cache["worldFileLastReloadTime"] = None
            cache["chapterInfoLastReloadTime"] = chapter_info_mtime

        world_file_path = cache["worldFilePath"]
        if not world_file_path:
            return None

        # 2. Check if the world file itself changed
        world_file_mtime = os.path.getmtime(world_file_path)
        if cache["worldFileLastReloadTime"] is None or cache["worldFileLastReloadTime"] < world_file_mtime:
            logger.log("WorldDataProvider - reload world data from world file: {}".format(world_file_path))
            try:
                with open(world_file_path, "r", encoding="utf-8") as f:
                    cache["worldData"] = world_parser.parse_world_file(f.read())
                cache["worldFileLastReloadTime"] = world_file_mtime
            except Exception as e:
                logger.log("WorldDataProvider - error reading world file: {}".format(e))
                return None

        return cache["worldData"]

    def clear_cache(self):
        self._project_cache = {}


# Singleton instance
provider = WorldDataProvider()
