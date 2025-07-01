import sys
from datetime import datetime
from pathlib import Path

import geopandas as gpd
from shapely.geometry import box

# ─── Utils ───────────────────────────────────────────────────────────────
from utils.config import load_default_config, ConfigError
from utils.paths import init_paths
from utils.file_manager import stage_files
from utils.notifications import safe_toast
from utils.constants import DEFAULT_CONFIG_NAME  # Back up for style

# ─── Parsers ────────────────────────────────────────────────────────────
from parsers.gml_parser import read_and_reproject, buffer_gdf
from parsers.txt_parser import parse_ticket_txt, parse_customer_details

# ─── Processing steps ────────────────────────────────────────────────────
from processing.clipping import clip_all_shapefiles
from processing.mapping import build_map, save_map
from processing.screenshot import screenshot_map
from processing.emailer import (
    compose_draft_gml,
    compose_draft_txt,
    save_and_open_draft
)


def main():
    # 0) Toast start
    safe_toast("UR Preview", "Processing started…", duration=3)

    # 1) Load & validate config
    try:
        cfg = load_default_config()  # looks for DEFAULT_CONFIG_NAME
    except ConfigError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)

    # 2) Initialize all paths
    paths = init_paths(cfg)
    DOWNLOAD_FOLDER = paths["DOWNLOAD_FOLDER"]
    RESULTS_DIR     = paths["RESULTS_DIR"]
    BASE_DIR        = paths["BASE_DIR"]

    # Ensure Results directory exists
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # 3) Stage incoming tickets
    ticket_file, xml_file, ticket_dir = stage_files(DOWNLOAD_FOLDER, RESULTS_DIR)
    if not ticket_file:
        print("No new GML or TXT tickets to process.")
        sys.exit(0)

    # 4) Assume main.py lives in project root
    PROJECT_ROOT = Path(__file__).resolve().parent

    shapefiles = {
        name: (PROJECT_ROOT / rel).resolve()
        for name, rel in cfg['SHAPEFILES'].items()
    }

    # 5) Parse work area from GML vs. TXT
    if ticket_file.suffix.lower() == ".gml":
        work_gdf = read_and_reproject(ticket_file)
        buf_gdf  = buffer_gdf(work_gdf)
        # parse customer info if XML present
        if xml_file:
            cust_name, cust_email, lon, lat = parse_customer_details(xml_file)
        else:
            cust_name, cust_email, lon, lat = (None, None, None, None)
    else:
        info, coord1, coord2 = parse_ticket_txt(ticket_file)
        lon, lat = coord1
        minx, maxx = sorted([coord1[0], coord2[0]])
        miny, maxy = sorted([coord1[1], coord2[1]])
        poly = box(minx, miny, maxx, maxy)
        work_gdf = gpd.GeoDataFrame(geometry=[poly], crs="EPSG:4326")
        buf_gdf  = buffer_gdf(work_gdf)

    # 6) Clip all shapefiles
    clipped = clip_all_shapefiles(shapefiles, buf_gdf)

    # 7) Determine if any features were found
    any_feats = any(len(df) > 0 for df in clipped.values())

    # 8) If no features, force the buffer outline to be visible
    if not any_feats:
        if not cfg.has_section("VISIBILITY"):
            cfg.add_section("VISIBILITY")
        cfg.set("VISIBILITY", "BUFFER_AREA", "True")

    # 9) Write summary report
    summary_path = ticket_dir / f"{ticket_file.stem}.txt"
    with summary_path.open("w") as f:
        f.write(f"Timestamp: {datetime.now()}\n")
        f.write(f"Ticket: {ticket_file.stem}\n")
        for layer, df in clipped.items():
            f.write(f"{layer}: {len(df)} feature(s)\n")

    # 10) Build & save Folium map
    map_obj   = build_map(cfg, work_gdf, buf_gdf, clipped)
    html_path = ticket_dir / f"{ticket_file.stem}.html"
    save_map(map_obj, html_path)

    # 11) Screenshot to PNG
    png_path = ticket_dir / f"{ticket_file.stem}.png"
    screenshot_map(html_path, png_path)

    # 12) Check for any features found
    any_feats = any(len(df) > 0 for df in clipped.values())

    # 13) Compose and open Outlook draft
    if ticket_file.suffix.lower() == ".gml":
        mail = compose_draft_gml(cfg, ticket_file, xml_file, png_path, any_feats)
    else:
        mail = compose_draft_txt(cfg, ticket_file, info, (coord1, coord2), png_path, any_feats)

    msg_path = save_and_open_draft(mail, ticket_dir)
    print(f"Draft saved to: {msg_path}")

    # 14) Toast completion
    safe_toast("UR Preview", "Processing complete!", duration=5)


if __name__ == "__main__":
    main()
