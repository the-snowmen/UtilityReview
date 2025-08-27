import os
from pathlib import Path
import win32com.client as win32
from typing import Optional, Tuple, Dict


def compose_draft_gml(
    cfg: Dict[str, str],
    ticket_file: Path,
    xml_file: Optional[Path],
    png_path: Path,
    any_feats: bool
) -> 'win32.MailItem':
    """
    Compose an Outlook draft for a GML-based ticket using plain-text COM
    with original greeting/body formatting.
    """
    # parse optional XML
    if xml_file and xml_file.exists():
        from parsers.txt_parser import parse_customer_details
        raw_name, to_addr, lon, lat = parse_customer_details(xml_file)
    else:
        raw_name, to_addr, lon, lat = None, None, None, None

    user = cfg['USER']
    mail_to = to_addr or user['Email']
    first_name = (raw_name or '').split()[0].capitalize() if raw_name else ''

    outlook = win32.Dispatch('Outlook.Application')
    mail = outlook.CreateItem(0)
    mail.Subject = f"TICKET: {ticket_file.stem}"
    mail.To = mail_to

    # greeting + body
    greet = f"Hello {first_name},\n\n" if first_name else "Hello,\n\n"
    if any_feats:
        body_txt = "Attached is a map of all features in your area (5% buffer). ALL LOCATIONS ARE APPROXIMATE.\n\n"
    else:
        body_txt = "There are no Everstream facilities in the given work area.\n\n"

    ticket_line = f"TICKET NO: {ticket_file.stem}\n\n"
    coord_line = f"Reference Coordinate: [{lon}, {lat}]\n\n" if lon is not None and lat is not None else "\n"

    body = greet + body_txt + ticket_line + coord_line

    # signature
    sig_lines = [
        "Thank you,",
        "",
        user['Name'],
        user['Title'],
        "Everstream®",
        user['Email']
    ]
    if user.get('Cell'):
        sig_lines.append(user['Cell'])
    sig_lines += ["", "**Automated**"]

    mail.BodyFormat = 1  # plain text
    mail.Body = body + "\n".join(sig_lines)
    mail.Attachments.Add(str(png_path))
    return mail


def compose_draft_txt(
    cfg: Dict[str, str],
    ticket_file: Path,
    info: Dict[str, str],
    coords: Tuple[Tuple[float, float], Tuple[float, float]],
    png_path: Path,
    any_feats: bool
) -> 'win32.MailItem':
    """
    Compose an Outlook draft for a TXT-based ticket using plain-text COM.
    """
    lon1, lat1 = coords[0]
    raw = info.get('Name') or info.get('Caller') or ''
    first = raw.split()[0].capitalize() if raw else ''
    mail_to = info.get('Email') or cfg['USER']['Email']

    outlook = win32.Dispatch('Outlook.Application')
    mail = outlook.CreateItem(0)
    #subj_type = "IUPPS Ticket" if 'iupps' in ticket_file.name.lower() else "Diggers Hotline Ticket"
    # mail.Subject = f"{subj_type}: {ticket_file.stem}"
    mail.Subject = ticket_file.stem.replace('_', ' ').strip()
    mail.To = mail_to

    # greeting + body
    greet = f"Hello {first},\n\n" if first else "Hello,\n\n"
    if any_feats:
        body_txt = "Attached is a map of all features in your area (5% buffer). ALL LOCATIONS ARE APPROXIMATE.\n\n"
    else:
        body_txt = "There are no Everstream facilities in the given work area.\n\n"

    ticket_line = f"Ticket NO: {ticket_file.stem.replace('_', ' ').strip()}\n"
    coord_line = f"Reference Coordinate: [{lon1}, {lat1}]\n\n"

    body = greet + body_txt + ticket_line + "\n" + coord_line

    # signature
    sig_lines = [
        "Thank you,",
        "",
        cfg['USER']['Name'],
        cfg['USER']['Title'],
        "Everstream®",
        cfg['USER']['Email']
    ]
    if cfg['USER'].get('Cell'):
        sig_lines.append(cfg['USER']['Cell'])
    sig_lines += ["", "**Automated**"]

    mail.BodyFormat = 1
    mail.Body = body + "\n".join(sig_lines)
    mail.Attachments.Add(str(png_path))
    return mail


def save_and_open_draft(mail: 'win32.MailItem', out_dir: Path) -> Path:
    """
    Save the MailItem as a .msg, open the containing folder, then open it in new Outlook.
    """
    filename = f"{mail.Subject.split(':')[-1].strip()}.msg"
    out_path = out_dir / filename
    try:
        mail.SaveAs(str(out_path), 3)
    except Exception:
        mail.Display()
        return out_path

    # open folder containing draft
    try:
        os.startfile(str(out_dir))
    except Exception:
        print(f"⚠️ Could not open folder {out_dir}")

    # open the draft
    try:
        os.startfile(str(out_path))
    except Exception:
        mail.Display()
    return out_path
