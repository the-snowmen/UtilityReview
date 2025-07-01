import configparser
from pathlib import Path
from typing import Dict, Tuple

import folium
import geopandas as gpd
from folium import Element


def build_map(
    cfg: configparser.ConfigParser,
    work_gdf: gpd.GeoDataFrame,
    buf_gdf: gpd.GeoDataFrame,
    clipped: Dict[str, gpd.GeoDataFrame]
) -> folium.Map:
    """
    Build a Folium map showing clipped layers, work area outline, and legend.

    Args:
        cfg: Loaded ConfigParser from changeme.txt.
        work_gdf: GeoDataFrame of the original work area.
        buf_gdf: GeoDataFrame containing the buffered polygon.
        clipped: Dict mapping layer names to their clipped GeoDataFrames.

    Returns:
        folium.Map instance ready to save.
    """
    # --- Extract styling from config ---
    color_cfg = cfg["COLORS"]
    layer_colors = {"CONDUIT": color_cfg.get("CONDUIT")}
    fiber_colors = {
        "aerial":      color_cfg.get("AERIAL"),
        "underground": color_cfg.get("UNDERGROUND"),
        "bridge":      color_cfg.get("BRIDGE"),
        "default":     color_cfg.get("UNKNOWN"),
    }
    work_area_color = color_cfg.get("WORK_AREA")

    opacity_cfg = cfg["OPACITIES"] if "OPACITIES" in cfg else {}
    conduit_opacity   = float(opacity_cfg.get("CONDUIT",   0.2))
    fiber_opacity     = float(opacity_cfg.get("FIBER",     0.3))
    work_area_opacity = float(opacity_cfg.get("WORK_AREA", 0.3))
    buffer_opacity    = work_area_opacity / 2.0

    weight_cfg = cfg["WEIGHTS"]
    conduit_weight   = int(weight_cfg.get("CONDUIT",   3))
    fiber_weight     = int(weight_cfg.get("FIBER",     4))
    work_area_weight = int(weight_cfg.get("WORK_AREA", 2))

    vis_cfg = cfg["VISIBILITY"] if "VISIBILITY" in cfg else {}
    show_buffer = cfg.getboolean("VISIBILITY", "BUFFER_AREA", fallback=False)

    struct_sym_cfg = cfg["STRUCTURE_SYMBOL"] if "STRUCTURE_SYMBOL" in cfg else {}
    struct_size     = int(struct_sym_cfg.get("SIZE",    12))
    struct_color    = struct_sym_cfg.get("COLOR",      "black")
    struct_opacity  = float(struct_sym_cfg.get("OPACITY",1.0))

    legend_labels = {k: v for k, v in cfg["LEGEND"].items()}

    # --- Determine map bounds from work area ---
    minx, miny, maxx, maxy = work_gdf.total_bounds
    sw = [miny, minx]
    ne = [maxy, maxx]

    # --- Initialize Folium map ---
    m = folium.Map(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri', control=False
    )

    # --- Style functions ---
    def fiber_style(feature):
        p = feature["properties"].get("placementt", "").lower()
        style = {"weight": fiber_weight, "fillOpacity": fiber_opacity}
        if "aerial" in p:
            style["color"] = fiber_colors["aerial"]
        elif "underground" in p:
            style["color"] = fiber_colors["underground"]
        elif "bridge" in p:
            style["color"] = fiber_colors["bridge"]
        else:
            style["color"] = fiber_colors["default"]
        return style

    # --- Add each clipped layer ---
    for name, gdf in clipped.items():
        if gdf.empty:
            continue

        if name == "FIBERCABLE":
            folium.GeoJson(
                gdf,
                style_function=fiber_style,
                tooltip=folium.GeoJsonTooltip(["placementt"], aliases=["Placement"])
            ).add_to(m)

        elif name == "CONDUIT":
            folium.GeoJson(
                gdf,
                style_function=lambda f, c=layer_colors["CONDUIT"]: {
                    "color": c,
                    "weight": conduit_weight,
                    "fillOpacity": conduit_opacity
                }
            ).add_to(m)

        elif name == "STRUCTURE":
            for _, row in gdf.iterrows():
                html_icon = f"""
                <div style="
                    font-size: {struct_size}px;
                    font-weight: bold;
                    width:       {struct_size}px;
                    height:      {struct_size}px;
                    line-height: {struct_size}px;
                    text-align:  center;
                    color:       {struct_color};
                    opacity:     {struct_opacity};
                ">
                    {row['symbol']}
                </div>
                """
                folium.Marker(
                    location=(row.geometry.y, row.geometry.x),
                    icon=folium.DivIcon(html=html_icon)
                ).add_to(m)

    # --- Work area outline ---
    folium.GeoJson(
        work_gdf,
        style_function=lambda f: {
            'color': work_area_color,
            'weight': work_area_weight,
            'fillOpacity': work_area_opacity
        }
    ).add_to(m)

    # --- Buffer outline if enabled ---
    if show_buffer:
        folium.GeoJson(
            buf_gdf,
            style_function=lambda f: {
                'color': work_area_color,
                'weight': work_area_weight,
                'fillOpacity': buffer_opacity
            }
        ).add_to(m)

    # --- Build a dynamic legend ---
    entries: list[Tuple[str, str]] = []
    # Conduit
    if not clipped.get("CONDUIT", gpd.GeoDataFrame()).empty:
        icon = f'<i style="background:{layer_colors["CONDUIT"]};width:12px;height:2px;display:inline-block;margin:0 6px;"></i>'
        entries.append((icon, legend_labels.get("CONDUIT", "Conduit")))

    # Structure symbols
    struct_df = clipped.get("STRUCTURE", gpd.GeoDataFrame())
    if not struct_df.empty:
        for sym in ['?','M','H','V']:
            if sym in struct_df['symbol'].unique():
                label = legend_labels.get(f"SYMBOL_{sym}", sym)
                span = (
                    f'<span style="'
                    f'display:inline-block;'
                    f'width:12px;'
                    f'height:12px;'
                    f'text-align:center;'
                    f'line-height:12px;'
                    f'font-weight:bold;'
                    f'color:{struct_color};'
                    f'">{sym}</span>'
                )
                entries.append((span, label))

    # Fiber types
    fiber_df = clipped.get("FIBERCABLE", gpd.GeoDataFrame())
    if not fiber_df.empty:
        types = fiber_df['placementt'].str.lower().unique()
        if any('aerial' in t for t in types):
            icon = f'<i style="background:{fiber_colors["aerial"]};width:12px;height:4px;display:inline-block;margin:0 6px;"></i>'
            entries.append((icon, legend_labels.get("AERIAL", "Aerial")))
        if any('underground' in t for t in types):
            icon = f'<i style="background:{fiber_colors["underground"]};width:12px;height:4px;display:inline-block;margin:0 6px;"></i>'
            entries.append((icon, legend_labels.get("UNDERGROUND", "Underground")))
        if any('bridge' in t for t in types):
            icon = f'<i style="background:{fiber_colors["bridge"]};width:12px;height:4px;display:inline-block;margin:0 6px;"></i>'
            entries.append((icon, legend_labels.get("BRIDGE", "Bridge")))

    # Work area legend entry
    wa_icon = f'<i style="background:{work_area_color};width:12px;height:12px;display:inline-block;margin:0 6px;"></i>'
    entries.append((wa_icon, legend_labels.get("WORK_AREA", "Work Area")))

    # Assemble legend HTML
    legend_html = """
    <div style="
        position: fixed; bottom:50px; left:50px;
        padding:8px;background:white;border:2px solid grey;
        font-size:14px;opacity:0.9;z-index:9999;">
        <b>Legend</b><br>
    """
    for icon, lbl in entries:
        legend_html += f"{icon} {lbl}<br>"
    legend_html += "</div>"
    m.get_root().html.add_child(Element(legend_html))

    # Fit to bounds and add layer control
    m.fit_bounds([sw, ne])
    folium.LayerControl().add_to(m)

    return m


def save_map(m: folium.Map, out_html: Path) -> None:
    """
    Save the Folium map to an HTML file.
    """
    m.save(out_html)
