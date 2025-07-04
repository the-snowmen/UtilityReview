import geopandas as gpd
import pandas as pd
from pathlib import Path
from typing import Dict


def clip_shapefile(name: str, shp_path: Path, buf_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Load and clip a single shapefile to the provided buffer area.

    Steps:
      1. Read via GeoPandas (with fallback for Latin-1 encoding).
      2. Reproject to EPSG:4326 if needed.
      3. Filter on locate_tog == 'Locate' for CONDUIT and STRUCTURE.
      4. Clip to buf_gdf.
      5. For STRUCTURE: coerce subtypecod to int and assign a symbol.
      6. Convert any datetime columns to ISO-8601 strings.

    Args:
        name: The layer key (e.g., 'CONDUIT', 'STRUCTURE', 'FIBERCABLE').
        shp_path: Path to the shapefile.
        buf_gdf: GeoDataFrame containing the buffer polygon.

    Returns:
        A clipped GeoDataFrame with any additional columns (e.g. 'symbol').
    """
    # 1) Load with fallback
    try:
        gdf = gpd.read_file(shp_path)
    except UnicodeDecodeError:
        gdf = gpd.read_file(shp_path, engine="fiona", encoding="latin-1")

    # 2) Reproject if needed
    if gdf.crs and gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)

    # 3) Filter locate_tog
    if name in ("CONDUIT", "STRUCTURE") and "locate_tog" in gdf.columns:
        gdf = gdf[gdf["locate_tog"] == "Locate"]

    # 4) Clip to buffer
    clipped = gpd.clip(gdf, buf_gdf).copy()

    # 5) STRUCTURE-specific symbol logic
    if name == "STRUCTURE":
        clipped["subtypecod"] = (
            pd.to_numeric(clipped.get("subtypecod", pd.Series()), errors="coerce")
              .fillna(0)
              .astype(int)
        )
        def pick_symbol(row):
            code  = row["subtypecod"]
            owner = str(row.get("owner", "")).lower()
            if code == 0:
                return "?"
            if code == 1:
                return "M"
            if code == 2:
                return "H"
            if code == 3:
                return "H" if "everstream" in owner else "V"
            return "?"
        clipped["symbol"] = clipped.apply(pick_symbol, axis=1)

    # 6) Convert datetime columns
    for col in clipped.columns:
        if pd.api.types.is_datetime64_any_dtype(clipped[col]):
            clipped[col] = clipped[col].dt.strftime("%Y-%m-%dT%H:%M:%S")

    return clipped


def clip_all_shapefiles(shapefiles: Dict[str, Path], buf_gdf: gpd.GeoDataFrame) -> Dict[str, gpd.GeoDataFrame]:
    """
    Clip multiple shapefiles according to the buffer GeoDataFrame.

    Args:
        shapefiles: Mapping of layer name to Path objects.
        buf_gdf: GeoDataFrame with a single polygon representing the buffer.

    Returns:
        Dict mapping each layer name to its clipped GeoDataFrame.
    """
    clipped_layers: Dict[str, gpd.GeoDataFrame] = {}
    for name, path in shapefiles.items():
        clipped_layers[name] = clip_shapefile(name, path, buf_gdf)
    return clipped_layers
