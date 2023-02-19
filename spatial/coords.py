# References:
# https://github.com/dickwxyz/CoordinatesConverter

import math
from math import cos, sin, asin, sqrt
from typing import Tuple

# Basic Parameters:
x_pi = 3.14159265358979324 * 3000.0 / 180.0
pi = 3.1415926535897932384626  # π
a = 6378245.0  # semi-major axis of WGS-84 ellipsoid
ee = 0.00669342162296594323  # oblateness of the earth

# Baidu Mercator Projection Parameters:
MC_BAND = [12890594.86, 8362377.87, 5591021, 3481989.83, 1678043.12, 0]
MC2LL = [
    [
        1.410526172116255e-8, 0.00000898305509648872, -1.9939833816331, 200.9824383106796, -187.2403703815547, 91.6087516669843, -23.38765649603339, 2.57121317296198, -0.03801003308653, 17337981.2
    ],
    [
        -7.435856389565537e-9, 0.000008983055097726239, -0.78625201886289, 96.32687599759846, -1.85204757529826, -59.36935905485877, 47.40033549296737, -16.50741931063887, 2.28786674699375, 10260144.86
    ],
    [
        -3.030883460898826e-8, 0.00000898305509983578, 0.30071316287616, 59.74293618442277, 7.357984074871, -25.38371002664745, 13.45380521110908, -3.29883767235584, 0.32710905363475, 6856817.37
    ],
    [
        -1.981981304930552e-8, 0.000008983055099779535, 0.03278182852591, 40.31678527705744, 0.65659298677277, -4.44255534477492, 0.85341911805263, 0.12923347998204, -0.04625736007561, 4482777.06
    ],
    [
        3.09191371068437e-9, 0.000008983055096812155, 0.00006995724062, 23.10934304144901, -0.00023663490511, -0.6321817810242, -0.00663494467273, 0.03430082397953, -0.00466043876332, 2555164.4
    ],
    [
        2.890871144776878e-9, 0.000008983055095805407, -3.068298e-8, 7.47137025468032, -0.00000353937994, -0.02145144861037, -0.00001234426596, 0.00010322952773, -0.00000323890364, 826088.5
    ]
]


def wgs84_to_gcj02(lng: float, lat: float) -> Tuple[float, float]:
    """
    Re-project the point from `wgs84` to `gcj02`.

    Args:
        lng (float): wgs84 CRS longitude
        lat (float): wgs84 CRS latitude

    Returns:
        tuple(float, float): (gcj02_lng, gcj02_lat)
    """
    if outside_of_china(lng, lat):
        return lng, lat

    d_lat = transform_lat(lng - 105.0, lat - 35.0)
    d_lng = transform_lng(lng - 105.0, lat - 35.0)
    rad_lat = lat / 180.0 * pi

    magic = math.sin(rad_lat)
    magic = 1 - ee*magic*magic
    sqrt_magic = math.sqrt(magic)

    d_lat = (d_lat * 180.0) / ((a * (1-ee)) / (magic*sqrt_magic) * pi)
    d_lng = (d_lng * 180.0) / (a / sqrt_magic * math.cos(rad_lat) * pi)
    mg_lat = lat + d_lat
    mg_lng = lng + d_lng
    return mg_lng, mg_lat


def gcj02_to_wgs84(lng: float, lat: float) -> Tuple[float, float]:
    """
    Re-project the point from `gcj02` to `wgs84`.

    Args:
        lng (float): gcj02 CRS longitude
        lat (float): gcj02 CRS latitude

    Returns:
        tuple(float, float): (wgs84_lng, wgs84_lat)
    """
    if outside_of_china(lng, lat):
        return lng, lat

    d_lat = transform_lat(lng - 105.0, lat - 35.0)
    d_lng = transform_lng(lng - 105.0, lat - 35.0)
    rad_lat = lat / 180.0 * pi

    magic = math.sin(rad_lat)
    magic = 1 - ee*magic*magic
    sqrt_magic = math.sqrt(magic)

    d_lat = (d_lat * 180.0) / ((a * (1-ee)) / (magic*sqrt_magic) * pi)
    d_lng = (d_lng * 180.0) / (a / sqrt_magic * math.cos(rad_lat) * pi)
    mg_lat = lat + d_lat
    mg_lng = lng + d_lng
    return lng*2 - mg_lng, lat*2 - mg_lat


def transform_lat(lng: float, lat: float) -> float:
    ret = (-100.0
           + 2.0*lng + 3.0*lat
           + 0.2*lat*lat + 0.1*lng*lat
           + 0.2*math.sqrt(math.fabs(lng)))

    ret += (20.0 * math.sin(6.0*lng*pi)
            + 20.0 * math.sin(2.0*lng*pi)) * 2.0 / 3.0

    ret += (20.0 * math.sin(lat*pi)
            + 40.0 * math.sin(lat/3.0*pi)) * 2.0 / 3.0

    ret += (160.0 * math.sin(lat/12.0*pi)
            + 320 * math.sin(lat*pi/30.0)) * 2.0 / 3.0
    return ret


def transform_lng(lng: float, lat: float) -> float:
    ret = (300.0
           + lng + 2.0*lat
           + 0.1*lng*lng + 0.1*lng*lat
           + 0.1*math.sqrt(math.fabs(lng)))

    ret += (20.0 * math.sin(6.0*lng*pi)
            + 20.0 * math.sin(2.0*lng*pi)) * 2.0 / 3.0

    ret += (20.0 * math.sin(lng*pi)
            + 40.0 * math.sin(lng/3.0*pi)) * 2.0 / 3.0

    ret += (150.0 * math.sin(lng/12.0*pi)
            + 300.0 * math.sin(lng/30.0*pi)) * 2.0 / 3.0
    return ret


def outside_of_china(lng: float, lat: float) -> bool:
    """
    Determine whether the point is on the outside of China.

    Args:
        lng (float): longitude in any of the CRS `wgs84`, `gcj02`, `bd09ll`
        lat (float): latitude in any of above CRS

    Returns:
        bool: True for outside of China, False otherwise
    """
    if lng < 72.004 or lng > 137.8347:
        return True
    if lat < 0.8293 or lat > 55.8271:
        return True
    return False


def gcj02_to_bd09ll(lng: float, lat: float) -> Tuple[float, float]:
    """
    Re-project the point from `gcj02` to `bd09ll`.

    Args:
        lng (float): gcj02 CRS longitude
        lat (float): gcj02 CRS latitude

    Returns:
        tuple(float, float): (bd09ll_lng, bd09ll_lat)
    """
    z = math.sqrt(lng*lng + lat*lat) + 0.00002 * math.sin(lat*x_pi)
    theta = math.atan2(lat, lng) + 0.000003 * math.cos(lng*x_pi)
    bd_lng = z*math.cos(theta) + 0.0065
    bd_lat = z*math.sin(theta) + 0.006
    return bd_lng, bd_lat


def bd09ll_to_gcj02(bd_lon: float, bd_lat: float) -> Tuple[float, float]:
    """
    Re-project the point from `bd09ll` to `gcj02`.

    Args:
        bd_lon (float): bd09ll CRS longitude
        bd_lat (float): bd09ll CRS latitude

    Returns:
        tuple(float, float): (gcj02_lng, gcj02_lat)
    """
    x = bd_lon - 0.0065
    y = bd_lat - 0.006
    z = math.sqrt(x*x + y*y) - 0.00002 * math.sin(y*x_pi)
    theta = math.atan2(y, x) - 0.000003 * math.cos(x*x_pi)
    gg_lng = z * math.cos(theta)
    gg_lat = z * math.sin(theta)
    return gg_lng, gg_lat


def wgs84_to_bd09ll(lon: float, lat: float) -> Tuple[float, float]:
    """
    Re-project the point from `wgs84` to `gcj02`,
    then from `gcj02` to `bd09ll`.

    Args:
        lon (float): wgs84 CRS longitude
        lat (float): wgs84 CRS latitude

    Returns:
        tuple(float, float): (bd09ll_lng, bd09ll_lat)
    """
    lon, lat = wgs84_to_gcj02(lon, lat)
    lon, lat = gcj02_to_bd09ll(lon, lat)
    return lon, lat


def bd09ll_to_wgs84(lon: float, lat: float) -> Tuple[float, float]:
    """
    Re-project the point from `bd09ll` to `gcj02`,
    then from `gcj02` to `wgs84`.

    Args:
        lon (float): bd09ll CRS longitude
        lat (float): bd09ll CRS latitude

    Returns:
        tuple(float, float): (wgs84_lng, wgs84_lat)
    """
    lon, lat = bd09ll_to_gcj02(lon, lat)
    lon, lat = gcj02_to_wgs84(lon, lat)
    return lon, lat


def bd09mc_to_bd09ll(x1: float, y1: float) -> Tuple[float, float]:
    """
    Re-project the point from `bd09mc` to `bd09ll`.

    Args:
        x1 (float): bd09mc CRS longitude
        y1 (float): bd09mc CRS latitude

    Returns:
        tuple(float, float): (bd09ll_lng, bd09ll_lat)
    """
    for cE in range(len(MC_BAND)):
        if y1 > MC_BAND[cE]:
            cF = MC2LL[cE]
            break
    xTemp = cF[0] + cF[1]*x1
    cC = y1 / cF[9]
    yTemp = cF[2] + cF[3]*cC + cF[4]*cC**2 + cF[5]*cC**3\
            + cF[6]*cC**4 + cF[7]*cC**5 + cF[8]*cC**6
    return xTemp, yTemp


def bd09mc_to_wgs84(x1: float, y1: float) -> Tuple[float, float]:
    """
    Re-project the point from `bd09mc` to `gcj02`,
    then from `gcj02` to `wgs84`.

    Args:
        x1 (float): bd09mc CRS longitude
        y1 (float): bd09mc CRS latitude
    Returns:
        tuple(float, float): (wgs84_lng, wgs84_lat)
    """
    x2, y2 = bd09mc_to_bd09ll(x1, y1)
    x3, y3 = bd09ll_to_wgs84(x2, y2)
    return x3, y3


def cal_distance(
    lon1: float,
    lat1: float,
    lon2: float,
    lat2: float
) -> float:
    """
    Calculate the `spherical` distance between two points.

    Args:
        lon1 (float): longitude of point 1
        lat1 (float): latitude of point 1
        lon2 (float): longitude of point 2
        lat2 (float): latitude of point 2

    Returns:
        float: spherical distance, in `kilometers`
    """
    d_lat = abs(lat1/180.0*pi - lat2/180.0*pi)
    d_lon = abs(lon1/180.0*pi - lon2/180.0*pi)
    a = sin(d_lat/2) * sin(d_lat/2)\
        + cos(lat1/180.0*pi) * cos(lat2/180.0*pi) * sin(d_lon/2) * sin(d_lon/2)
    dist = 2 * 6378.137 * asin(sqrt(a))
    return dist
