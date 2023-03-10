import logging
import os

from processor.repository import Repo


class Validator(object):
    @classmethod
    def validate_settings(cls) -> None:
        cls._validate_spider_settings()
        cls._validate_path_settings()
        cls._validate_api_settings()
        cls._validate_aoi_filter_settings()
        logging.warning("(1/6) Settings validation complete.")

    @classmethod
    def validate_file(cls) -> None:
        """
        `POI csv` should have the following columns:
        - Compulsory:
            - name (str): POI name
            - lng (float): POI's longitude
            - lat (float): POI's latitude
        - Optional:
            - prim_ind (str): POI's primary industry classification
            - sec_ind (str):  POI's secondary industry classification
        """
        for col in ["name", "lng", "lat"]:
            if not col in Repo.file.columns:
                raise ValueError(f'Column "{col}" is missing.')
        cls._check_optional_col("prim_ind", Repo._prim_ind)
        cls._check_optional_col("sec_ind", Repo._sec_ind)
        logging.warning("(2/6) POI csv file validation complete.")

    @classmethod
    def _validate_spider_settings(cls) -> None:
        # PROXY_ENABLED, USE_FIRST_UID is bool type
        cls._verify_value_type(Repo._proxy_enabled, "PROXY_ENABLED", bool)
        cls._verify_value_type(Repo._use_first_uid, "USE_FIRST_UID", bool)
        # UPDATE_INTERVAL must be a positive number
        cls._verify_non_negative_num(Repo._update_interval, "UPDATE_INTERVAL")

    @staticmethod
    def _validate_path_settings() -> None:
        poi_dir = Repo._poi_csv_path
        aoi_dir = Repo._aoi_shp_path
        aoi_parent_dir = os.path.dirname(aoi_dir)
        # POI directory existence
        if not os.path.exists(poi_dir):
            raise FileNotFoundError(f'POI_CSV_PATH not found: "{poi_dir}".')
        if not poi_dir.endswith(".csv"):
            raise ValueError(f'"{poi_dir}" must be a csv file.')
        # If AOI shp parent directory does not exist, create it
        if not aoi_dir.endswith(".shp"):
            raise ValueError(f'"{aoi_dir}" must be a shp file.')
        if not os.path.exists(aoi_parent_dir):
            os.makedirs(aoi_parent_dir)
            logging.warning("(0/6) AOI_SHP_PATH parent directory created.")

    @classmethod
    def _validate_api_settings(cls) -> None:
        # AK_LIST must be a list of strings
        cls._verify_value_type(Repo._ak_list, "AK_LIST", list)
        if not Repo._ak_list:
            raise ValueError("AK_LIST must not be empty.")
        for ak in Repo._ak_list:
            cls._verify_value_type(ak, "AK", str)
        # API_PARAMS rules:
        # industry parameter must be a string
        cls._verify_value_type(Repo._prim_ind, "prim_ind", str)
        cls._verify_value_type(Repo._sec_ind, "sec_ind", str)
        # radius parameter must be a positive number
        cls._verify_non_negative_num(Repo._radius, "radius")
        # radius_limit must be one of 'true' or 'false'
        if not Repo._radius_limit in ["true", "false"]:
            raise ValueError('"radius_limit" must be "true" or "false".')
        # crs must be one of 'gcj02', 'bd09' or 'wgs84'
        if not Repo._crs in ["gcj02", "bd09", "wgs84"]:
            raise ValueError('"crs" must be "gcj02", "bd09" or "wgs84".')

    @classmethod
    def _validate_aoi_filter_settings(cls) -> None:
        # area limit must be a positive number
        cls._verify_non_negative_num(Repo._min_aoi_area, "min_aoi_area")
        cls._verify_non_negative_num(Repo._max_aoi_area, "max_aoi_area")
        # minimum similarity must be smaller than 1
        cls._verify_value_type(Repo._min_similarity, "min_similarity", float | int)
        if Repo._min_similarity >= 1:
            raise ValueError('"min_similarity" must not be more than 1.')
        # sorting values must be one of 0 or 1 (or -1 for 'sort_by_area')
        for sorting_type, value in Repo._sortings.items():
            if sorting_type == "sort_by_area":
                if not value in [0, 1, -1]:
                    raise ValueError(f'"{sorting_type}" must be 0 or ±1.')
            elif not value in [0, 1]:
                raise ValueError(f'"{sorting_type}" must be 0 or 1.')
        # at least one kind of sorting must be enabled
        if not any(Repo._sortings.values()):
            raise ValueError("Sorting values must not be all 0.")

    @staticmethod
    def _check_optional_col(name: str, value: str) -> None:
        if value == "AS_VAR":
            if not name in Repo.file.columns:
                raise ValueError(f'Column "{name}" is missing.')

    @classmethod
    def _verify_non_negative_num(cls, value: any, name: str) -> None:
        cls._verify_value_type(value, name, float | int)
        if value < 0:
            raise ValueError(f'"{name}" must be a non-negative number.')

    @staticmethod
    def _verify_value_type(
        value: any, name: str, type: bool | int | str | list | dict
    ) -> None:
        if not isinstance(value, type):
            raise TypeError(f'"{name}" must be a {str(type).replace("|", "or")}.')
