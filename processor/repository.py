import logging

import pandas as pd


class Repo(object):
    @classmethod
    def import_settings(cls, settings: dict) -> None:
        cls._import_settings(settings)
        logging.warning("# ---------- Initialization ---------- #")

    @classmethod
    def load_file(cls) -> None:
        cls.file = pd.read_csv(cls._poi_csv_path, encoding="utf-8")

    @classmethod
    def _import_settings(cls, settings: dict) -> None:
        # Spider settings
        cls._proxy_enabled = settings.get("PROXY_ENABLED")
        cls._update_interval = settings.get("UPDATE_INTERVAL")
        cls._use_first_uid = settings.get("USE_FIRST_UID")
        # File path settings
        cls._poi_csv_path = settings.get("POI_CSV_PATH")
        cls._aoi_shp_path = settings.get("AOI_SHP_PATH")
        # Baidu API settings
        cls._ak_list = settings.get("AK_LIST")
        cls._prim_ind = settings.get("API_PARAMS", {}).get("prim_ind")
        cls._sec_ind = settings.get("API_PARAMS", {}).get("sec_ind")
        cls._radius = settings.get("API_PARAMS", {}).get("radius")
        cls._radius_limit = settings.get("API_PARAMS", {}).get("radius_limit")
        cls._crs = settings.get("API_PARAMS", {}).get("crs")
        # AOI filter settings
        cls._min_aoi_area = settings.get("FILTER_RULES", {}).get("min_aoi_area")
        cls._max_aoi_area = settings.get("FILTER_RULES", {}).get("max_aoi_area")
        cls._min_similarity = settings.get("FILTER_RULES", {}).get("min_similarity")
        cls._sortings = {
            sorting: settings.get("FILTER_RULES", {}).get(sorting)
            for sorting in [
                "sort_by_search_rank",
                "sort_by_area",
                "sort_by_distance",
                "sort_by_similarity",
            ]
        }
