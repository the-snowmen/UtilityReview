# utils/constants.py

"""
Default constants and fallback values for the UR Preview application.
"""

# Default config filename
DEFAULT_CONFIG_NAME = "config.json"

# Folium tile service
TILES_URL = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
TILES_ATTRIBUTION = "Esri"

# Default styling values (used if OPACITIES or WEIGHTS sections are missing)
DEFAULT_OPACITIES = {
    "CONDUIT":    0.2,
    "FIBER":      0.3,
    "WORK_AREA":  0.3,
}

DEFAULT_WEIGHTS = {
    "CONDUIT":    3,
    "FIBER":      4,
    "WORK_AREA":  2,
}

DEFAULT_VISIBILITY = {
    "BUFFER_AREA": False
}

DEFAULT_STRUCTURE_SYMBOL = {
    "SIZE": 12,
    "COLOR": "black",
    "OPACITY": 1.0,
    "WEIGHT": 1
}

DEFAULT_LEGEND_LABELS = {
    "CONDUIT":    "Conduit",
    "AERIAL":     "Aerial Cable",
    "UNDERGROUND":"Underground Cable",
    "BRIDGE":     "Bridge-mounted Cable",
    "WORK_AREA":  "Work Area",
    "SYMBOL_?":   "Unknown Structure",
    "SYMBOL_M":   "Manhole",
    "SYMBOL_H":   "Handhole",
    "SYMBOL_V":   "Vault",
}

__all__ = [
    "DEFAULT_CONFIG_NAME",
    "TILES_URL", "TILES_ATTRIBUTION",
    "DEFAULT_OPACITIES", "DEFAULT_WEIGHTS",
    "DEFAULT_VISIBILITY", "DEFAULT_STRUCTURE_SYMBOL",
    "DEFAULT_LEGEND_LABELS",
]
