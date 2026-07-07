"""Conversions CRS explicites pour les donnees SlowVaud."""

from __future__ import annotations

import math

from pyproj import Transformer
from shapely.geometry import Point
from shapely.ops import transform

CRS_WGS84 = "EPSG:4326"
CRS_LV95 = "EPSG:2056"
CRS_WEB_MERCATOR = "EPSG:3857"

WGS84_TO_LV95 = Transformer.from_crs(CRS_WGS84, CRS_LV95, always_xy=True)
LV95_TO_WGS84 = Transformer.from_crs(CRS_LV95, CRS_WGS84, always_xy=True)


def wgs84_to_lv95(lon: float, lat: float) -> tuple[float, float]:
    """Convertir WGS84 lon/lat vers LV95 EPSG:2056 avec pyproj."""
    east, north = WGS84_TO_LV95.transform(lon, lat)
    return float(east), float(north)


def buffer_bbox_wgs84(lon: float, lat: float, buffer_m: float) -> tuple[float, float, float, float]:
    """Calculer une emprise WGS84 depuis un buffer metrique en LV95."""
    east, north = wgs84_to_lv95(lon, lat)
    buffered_lv95 = Point(east, north).buffer(buffer_m)
    buffered_wgs84 = transform(LV95_TO_WGS84.transform, buffered_lv95)
    min_lon, min_lat, max_lon, max_lat = buffered_wgs84.bounds
    return float(min_lon), float(min_lat), float(max_lon), float(max_lat)


def lonlat_to_tile(lon: float, lat: float, zoom: int) -> tuple[int, int]:
    """Convertir lon/lat en indices de tuile XYZ Web Mercator."""
    lat = max(min(lat, 85.05112878), -85.05112878)
    n = 2**zoom
    x = int((lon + 180.0) / 360.0 * n)
    y = int(
        (1.0 - math.log(math.tan(math.radians(lat)) + 1.0 / math.cos(math.radians(lat))) / math.pi)
        / 2.0
        * n
    )
    return x, y


def tile_range_for_bbox(
    bbox: tuple[float, float, float, float], zoom: int
) -> tuple[int, int, int, int]:
    """Retourner x_min, x_max, y_min, y_max pour une emprise WGS84."""
    min_lon, min_lat, max_lon, max_lat = bbox
    x1, y1 = lonlat_to_tile(min_lon, max_lat, zoom)
    x2, y2 = lonlat_to_tile(max_lon, min_lat, zoom)
    return min(x1, x2), max(x1, x2), min(y1, y2), max(y1, y2)


def wmts_pixel_size_m(lat: float, zoom: int) -> float:
    """Resolution estimee d'une tuile Web Mercator en metres par pixel."""
    return 156543.03392804097 * math.cos(math.radians(lat)) / (2**zoom)
