import pyproj
from shapely import wkt
from shapely.ops import transform
from shapely.geometry.base import BaseGeometry
from shapely.geometry import LineString, Polygon
from spatial.coords import cal_distance


def within_distance(
    lng1: float,
    lat1: float,
    lng2: float,
    lat2: float,
    distance: int = 1
) -> bool:
    """
    Determine whether the spherical distance between `(lng1, lat1)` and `(lng2, lat2)`
    is less than the given distance (unit: `kilometers`).
    """
    return cal_distance(lng2, lat2, lng1, lat1) <= distance


def points_to_polygon(points: list) -> Polygon:
    """
    Convert a list of points to a `shapely` polygon.
    """
    return Polygon(LineString(points))


def wkt_to_geometry(wkt_str: str) -> BaseGeometry:
    """
    Convert `wkt` string to `shapely` geometry.
    """
    return wkt.loads(wkt_str)


def wgs84_to_wgs84utm50n(geometry: BaseGeometry) -> BaseGeometry:
    """
    Transform the geometry projection from `wgs84` to `wgs84_utm50n`.
    """
    wgs84 = pyproj.CRS('EPSG:4326')
    wgs84_utm50n = pyproj.CRS('EPSG:32650')
    project = pyproj.Transformer.from_crs(
        wgs84, wgs84_utm50n, always_xy=True).transform
    return transform(project, geometry)
