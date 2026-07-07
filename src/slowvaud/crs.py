"""Conversions CRS explicites pour les donnees SlowVaud."""

from __future__ import annotations

from pyproj import Transformer

CRS_WGS84 = "EPSG:4326"
CRS_LV95 = "EPSG:2056"

WGS84_TO_LV95 = Transformer.from_crs(CRS_WGS84, CRS_LV95, always_xy=True)


def wgs84_to_lv95(lon: float, lat: float) -> tuple[float, float]:
    """Convertir WGS84 lon/lat vers LV95 EPSG:2056 avec pyproj."""
    east, north = WGS84_TO_LV95.transform(lon, lat)
    return float(east), float(north)
