import sys
from datetime import datetime
from pathlib import Path
import time

import math
import geopandas as gpd
from shapely.geometry import box

# ─── Utils ────────────────────────────────────────────────────────────
from utils.config import load_default_config, ConfigError
from utils.paths import init_paths
from utils.file_manager import stage_files
from utils.notifications import safe_toast
from utils.constants import DEFAULT_CONFIG_NAME

# ─── Parsers ───────────────────────────────────────────
from parsers.gml_parser import read_and_reproject, buffer_gdf
from parsers.txt_parser import parse_ticket_txt, parse_customer_details

# ─── Processing steps ──────────────────────────────────
from processing.clipping import clip_all_shapefiles
from processing.mapping import build_map, save_map
from processing.screenshot import screenshot_map
from processing.emailer import (
    compose_draft_gml,
    compose_draft_txt,
    save_and_open_draft
)

MIN_SIZE_M = 30  # Minimum dimension in meters for txt workflow

def enforce_min_size_deg(geom):
    minx, miny, maxx, maxy = geom.bounds
    center_lat = (miny + maxy) / 2.0
    deg_per_m_lat = 1.0 / 111_320
    deg_per_m_lon = 1.0 / (111_320 * math.cos(math.radians(center_lat)))
    width_deg = maxx - minx
    height_deg = maxy - miny
    req_w = MIN_SIZE_M * deg_per_m_lon
    req_h = MIN_SIZE_M * deg_per_m_lat
    expand_x = max(0, (req_w - width_deg) / 2.0)
    expand_y = max(0, (req_h - height_deg) / 2.0)
    return box(minx - expand_x, miny - expand_y, maxx + expand_x, maxy + expand_y)

def timed_step(label, log_file, func, *args, **kwargs):
    start = time.time()
    result = func(*args, **kwargs)
    elapsed = time.time() - start
    print(f"{label} took {elapsed:.2f} sec")
    with log_file.open("a") as f:
        f.write(f"{label} took {elapsed:.2f} sec\n")
    return result

def main():
    script_start = time.time()

    # Toast start
    safe_toast("UR Preview", "Processing started…", duration=3)

    try:
        cfg = load_default_config()
    except ConfigError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)

    paths = init_paths(cfg)
    DOWNLOAD_FOLDER = paths["DOWNLOAD_FOLDER"]
    RESULTS_DIR     = paths["RESULTS_DIR"]
    BASE_DIR        = paths["BASE_DIR"]
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    ticket_file, xml_file, ticket_dir = stage_files(DOWNLOAD_FOLDER, RESULTS_DIR)
    if not ticket_file:
        print("No new GML or TXT tickets to process.")
        sys.exit(0)

    timing_log = ticket_dir / f"{ticket_file.stem}_timing.txt"
    with timing_log.open("w") as f:
        f.write(f"Timing log for ticket {ticket_file.stem}\n")
        f.write(f"Started at {datetime.now()}\n\n")

    PROJECT_ROOT = Path(__file__).resolve().parent
    shapefiles = {
        name: (PROJECT_ROOT / rel).resolve()
        for name, rel in cfg['SHAPEFILES'].items()
    }

    if ticket_file.suffix.lower() == ".gml":
        work_gdf = timed_step("Read and reproject GML", timing_log, read_and_reproject, ticket_file)
        buf_gdf  = timed_step("Buffer geometry", timing_log, buffer_gdf, work_gdf)
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
        work_gdf.geometry = work_gdf.geometry.apply(enforce_min_size_deg)
        buf_gdf  = timed_step("Buffer geometry", timing_log, buffer_gdf, work_gdf)

    clipped = timed_step("Clip shapefiles", timing_log, clip_all_shapefiles, shapefiles, buf_gdf)
    any_feats = any(len(df) > 0 for df in clipped.values())

    if not any_feats:
        if not cfg.has_section("VISIBILITY"):
            cfg.add_section("VISIBILITY")
        cfg.set("VISIBILITY", "BUFFER_AREA", "True")

    summary_path = ticket_dir / f"{ticket_file.stem}.txt"
    with summary_path.open("w") as f:
        f.write(f"Timestamp: {datetime.now()}\n")
        f.write(f"Ticket: {ticket_file.stem}\n")
        for layer, df in clipped.items():
            f.write(f"{layer}: {len(df)} feature(s)\n")

    map_obj = timed_step("Build folium map", timing_log, build_map, cfg, work_gdf, buf_gdf, clipped)
    html_path = ticket_dir / f"{ticket_file.stem}.html"
    timed_step("Save map HTML", timing_log, save_map, map_obj, html_path)

    png_path = ticket_dir / f"{ticket_file.stem}.png"
    timed_step("Take screenshot", timing_log, screenshot_map, html_path, png_path)

    if ticket_file.suffix.lower() == ".gml":
        mail = timed_step("Compose Outlook GML draft", timing_log, compose_draft_gml, cfg, ticket_file, xml_file, png_path, any_feats)
    else:
        mail = timed_step("Compose Outlook TXT draft", timing_log, compose_draft_txt, cfg, ticket_file, info, (coord1, coord2), png_path, any_feats)

    timed_step("Save + open Outlook draft", timing_log, save_and_open_draft, mail, ticket_dir)
    safe_toast("UR Preview", "Processing complete!", duration=5)

    total_elapsed = time.time() - script_start
    with timing_log.open("a") as f:
        f.write(f"\nTotal time: {total_elapsed:.2f} sec\n")

if __name__ == "__main__":
    main()
