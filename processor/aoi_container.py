import logging
from difflib import SequenceMatcher

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from shapely.geometry import Point, Polygon

from processor.repository import Repo
from spatial.geometry import wgs84_to_wgs84utm50n


class AOI(object):
    def __init__(self, rank: int, uid_name: str, geometry: Polygon) -> None:
        self.uid_name = uid_name
        self.geometry = geometry
        self.search_rank = rank
        self.area = self._area() / 1000000  # convert to square kilometers

    def _area(self) -> float:
        return wgs84_to_wgs84utm50n(self.geometry).area  # unit: square meters

    def _not_too_big_or_too_small(self) -> bool:
        return (self.area >= Repo._min_aoi_area) and (self.area <= Repo._max_aoi_area)

    def _not_too_different(self) -> bool:
        """
        Return True either `sort_by_similarity` is disabled,
        or the similarity between the names of the AOI and the POI
        is above the threshold when similarity sorting is enabled.
        """
        return (Repo._sortings.get("sort_by_similarity") == 0) or (
            self.similarity >= Repo._min_similarity
        )


class AOI_list(object):
    def __init__(self, idx: int) -> None:
        self.poi_name = Repo.file.loc[idx, "name"]
        self.p_lng = Repo.file.loc[idx, "lng_wgs84"]
        self.p_lat = Repo.file.loc[idx, "lat_wgs84"]
        self.aoi_list = []

    def _append(self, aoi: AOI) -> None:
        aoi = self._add_poi_related_property(aoi)
        if self._validate_aoi(aoi):
            self.aoi_list.append(aoi)

    def _validate_aoi(self, aoi: AOI) -> bool:
        def bbox_contains_poi() -> bool:
            """
            Check if the `bounding box` of AOI contains the corresponding POI.
            """
            lng1, lat1, lng2, lat2 = aoi.geometry.bounds
            if lng1 <= self.p_lng <= lng2 and lat1 <= self.p_lat <= lat2:
                return True
            else:
                return False

        return (
            bbox_contains_poi()
            and aoi._not_too_big_or_too_small()
            and aoi._not_too_different()
        )

    def _get_best_aoi(self) -> AOI:
        if self.aoi_list:
            weighted_rank = self._weighted_rank()
            best_aoi_idx = np.argmin(weighted_rank)
            return self.aoi_list[best_aoi_idx]

    def _sort_by_search_rank(self) -> NDArray:
        return self._get_rank(lambda aoi: aoi.search_rank)

    def _sort_by_area(self) -> NDArray:
        """
        Sort in ascending order if `sort_by_area` is 1, in descending order if -1.
        """
        return self._get_rank(lambda aoi: Repo._sortings.get("sort_by_area") * aoi.area)

    def _sort_by_distance(self) -> NDArray:
        return self._get_rank(lambda aoi: aoi.distance)

    def _sort_by_similarity(self) -> NDArray:
        return self._get_rank(lambda aoi: -aoi.similarity)  # descending

    def _get_rank(self, func: callable) -> NDArray:
        """
        Return an rank array [r1, r2, ... rn] for an AOI property list
        [aoi_1.property, aoi_2.property, ... aoi_n.property],
        such that aoi_i.property is the ri-th smallest element.
        """
        return np.argsort(np.argsort([func(aoi) for aoi in self.aoi_list]))

    def _weighted_rank(self) -> NDArray:
        ranks = []
        for sorting, value in Repo._sortings.items():
            if value != 0:
                ranks.append(getattr(self, f"_{sorting}")())
        values = [value for value in Repo._sortings.values() if value != 0]
        weights = np.array(values) / np.abs(values).sum()
        return sum([rank * weight for rank, weight in zip(ranks, weights)])

    def _add_poi_related_property(self, aoi: AOI) -> AOI:
        def cal_distance(aoi: AOI) -> float:
            """
            Plane distance between the POI and the AOI
            in Wgs84-Utm50N projection.
            """
            geometry = wgs84_to_wgs84utm50n(aoi.geometry)
            point = wgs84_to_wgs84utm50n(Point(self.p_lat, self.p_lng))
            return geometry.distance(point)

        def cal_similarity(aoi: AOI) -> float:
            """
            Text similarity is calculated using difflib `SequenceMatcher`. For its algorithm,
            see https://stackoverflow.com/questions/35517353/how-does-pythons-sequencematcher-work
            """
            return SequenceMatcher(None, aoi.uid_name, self.poi_name).ratio()

        if Repo._sortings.get("sort_by_distance"):
            aoi.distance = cal_distance(aoi)
        if Repo._sortings.get("sort_by_similarity"):
            aoi.similarity = cal_similarity(aoi)
        return aoi


class AOIContainer(object):
    @classmethod
    def mold(cls) -> None:
        cls._dict = {idx: AOI_list(idx) for idx in Repo.file.index}
        logging.warning("(6/6) AOIContainer is ready.")

    @classmethod
    def append(cls, idx: int, rank: int, uid_name: str, geometry: Polygon) -> None:
        """
        Store an AOI in the `AOI_list` of its corresponding POI,
        if this AOI satisfies all the following requirements:
            - The bounding box of the AOI contains the corresponding POI.
            - The AOI's area is not too big or too small.
            - The AOI's name is not too different from the POI's name.
        """
        aoi = AOI(rank, uid_name, geometry)
        cls._dict[idx]._append(aoi)

    @classmethod
    def get_best_aoi(cls, idx: int) -> AOI:
        return cls._dict[idx]._get_best_aoi()
