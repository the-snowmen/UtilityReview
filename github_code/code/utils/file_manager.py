import shutil
from pathlib import Path
from typing import Optional, Tuple


def get_latest_file(folder: Path, ext: str) -> Optional[Path]:
    """
    Return the most recently created file in `folder` with the given extension.

    Args:
        folder: Directory to search.
        ext: File extension to filter by (e.g., '.gml').

    Returns:
        Path to the newest file matching `ext`, or None if none found.
    """
    if not folder.is_dir():
        return None

    candidates = [p for p in folder.iterdir() if p.suffix.lower() == ext.lower()]
    if not candidates:
        return None

    # Choose by creation time (cTime)
    latest = max(candidates, key=lambda p: p.stat().st_ctime)
    return latest


def stage_files(download_folder: Path, results_dir: Path) -> Tuple[Optional[Path], Optional[Path], Optional[Path]]:
    """
    Move the latest .gml or .txt ticket file from `download_folder` into a new subfolder under `results_dir`.

    - Looks for files ending in .gml, or .txt containing 'iupps' or 'diggers'.
    - Moves the ticket file (and matching XML if .gml) into a timestamped folder.

    Args:
        download_folder: Path where new ticket files arrive.
        results_dir: Path under which to create per-ticket result folders.

    Returns:
        A tuple of (ticket_file, xml_file, ticket_dir), where:
          - ticket_file: Path to the moved .gml or .txt file (None if none found).
          - xml_file: Path to the moved .xml file if a .gml ticket had one (else None).
          - ticket_dir: Path to the directory created for this ticket (else None).
    """
    if not download_folder.is_dir():
        return None, None, None

    # Gather candidates
    candidates = []
    for p in download_folder.iterdir():
        name = p.name.lower()
        if p.suffix.lower() == '.gml':
            candidates.append(p)
        elif p.suffix.lower() == '.txt' and ('iupps' in name or 'diggers' in name):
            candidates.append(p)

    if not candidates:
        return None, None, None

    latest = max(candidates, key=lambda p: p.stat().st_ctime)
    base = latest.stem
    ticket_dir = results_dir / base
    ticket_dir.mkdir(parents=True, exist_ok=True)

    # Move the ticket file
    dest_ticket = ticket_dir / latest.name
    shutil.move(str(latest), str(dest_ticket))

    xml_path = None
    # If .gml, also move matching .xml
    if dest_ticket.suffix.lower() == '.gml':
        xml_src = download_folder / f"{base}.xml"
        if xml_src.exists():
            dest_xml = ticket_dir / xml_src.name
            shutil.move(str(xml_src), str(dest_xml))
            xml_path = dest_xml

    return dest_ticket, xml_path, ticket_dir
