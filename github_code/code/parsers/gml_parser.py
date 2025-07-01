# parsers/gml_parser.py
import geopandas as gpd
from shapely.ops import unary_union
from pathlib import Path

def read_and_reproject(gml_path: Path) -> gpd.GeoDataFrame:
    """
    Read a GML file into a GeoDataFrame and reproject to EPSG:4326 if needed.

    Args:
        gml_path: Path to the .gml file.

    Returns:
        GeoDataFrame in EPSG:4326.
    """
    gdf = gpd.read_file(gml_path)
    if gdf.crs and gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)
    return gdf


def buffer_gdf(gdf: gpd.GeoDataFrame, pct: float = 0.03) -> gpd.GeoDataFrame:
    """
    Create a buffer around the union of all geometries in gdf.

    Args:
        gdf: GeoDataFrame to buffer.
        pct: Fraction of the max span (in degrees or projection units) to use as buffer distance.

    Returns:
        A new GeoDataFrame containing the buffered polygon.
    """
    # 1) Union all geometries
    union_geom = unary_union(gdf.geometry)
    # 2) Compute span
    minx, miny, maxx, maxy = gdf.total_bounds
    dx, dy = maxx - minx, maxy - miny
    # 3) Determine buffer distance
    if gdf.crs.is_geographic:
        dist = max(dx, dy) * pct
    else:
        dist = max(dx, dy) * pct
    # 4) Buffer and wrap in GeoDataFrame
    buffered = union_geom.buffer(dist)
    return gpd.GeoDataFrame(geometry=[buffered], crs=gdf.crs)
