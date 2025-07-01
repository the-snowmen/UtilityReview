# parsers/txt_parser.py
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Tuple, Dict, Optional

def parse_ticket_txt(txt_path: Path) -> Tuple[Dict[str, str], Tuple[float, float], Tuple[float, float]]:
    """
    Parse a Diggers/IUPPS ticket TXT for caller info and two coordinate pairs.

    Returns:
        info: dict of all key:value lines
        coord1: (lon, lat)
        coord2: (lon, lat)
    """
    info: Dict[str,str] = {}
    with txt_path.open(encoding='utf-8', errors='ignore') as f:
        for line in f:
            if ':' not in line:
                continue
            key, val = line.split(':', 1)
            info[key.strip()] = val.strip()

    # Extract and convert coordinates
    lon1, lat1 = map(float, info.get('Coordinate1', '0,0').split(','))
    lon2, lat2 = map(float, info.get('Coordinate2', '0,0').split(','))
    return info, (lon1, lat1), (lon2, lat2)


def parse_customer_details(xml_file: Path) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    Parse OneCall XML for customer name, email, longitude, latitude.

    Returns:
        (name, email, lon, lat) or (None, None, None, None) on error.
    """
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        ns = {'onecall': 'http://www.pelicancorp.com/onecall'}
        cust = root.find('onecall:CustomerDetails', ns)
        loc = root.find('onecall:LocationDetails', ns)
        name = cust.find('onecall:Name', ns).text if cust is not None else None
        email = cust.find('onecall:EmailAddress', ns).text if cust is not None else None
        lon = loc.find('onecall:Longitude', ns).text if loc is not None else None
        lat = loc.find('onecall:Latitude', ns).text if loc is not None else None
        return name, email, lon, lat
    except Exception:
        return None, None, None, None
