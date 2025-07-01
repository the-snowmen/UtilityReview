import os
import sys
from pathlib import Path


def get_base_dir() -> Path:
    """
    Returns the directory containing bundled resources when frozen by PyInstaller,
    or the module's directory when running as a .py file.
    """
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    try:
        return Path(__file__).resolve().parent
    except NameError:
        return Path.cwd()


def get_run_dir() -> Path:
    """
    Returns the current working directory where the script was launched.
    """
    return Path.cwd()


def get_results_dir(run_dir: Path, results_dir_cfg: str) -> Path:
    """
    Resolve and create the results directory based on the config value.

    Args:
        run_dir: Path where the app is running.
        results_dir_cfg: Raw string from config for ResultsDir.

    Returns:
        Absolute Path to the results directory, ensuring it exists.
    """
    path = Path(results_dir_cfg)
    if not path.is_absolute():
        path = (run_dir / path).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_download_folder(raw_download: str, run_dir: Path) -> Path:
    """
    Resolve and create the download folder based on the config value.

    Logic:
    1) Expand ~ and environment variables.
    2) If not absolute, interpret relative to run_dir.
    3) If the path doesn't exist, fall back to ~/Downloads.
    4) Ensure the folder exists.

    Args:
        raw_download: Raw string from config for DownloadFolder.
        run_dir: Path where the app is running.

    Returns:
        Absolute Path to the download folder, ensuring it exists.
    """
    # 1) expand ~ and env-vars
    dl = Path(os.path.expanduser(os.path.expandvars(raw_download)))

    # 2) if it’s not absolute, interpret it relative to run_dir
    if not dl.is_absolute():
        dl = (run_dir / dl).resolve()

    # 3) if that path still doesn’t exist, fall back to ~/Downloads
    if not dl.exists():
        dl = Path.home() / "Downloads"

    # 4) ensure it exists
    dl.mkdir(parents=True, exist_ok=True)
    return dl


def init_paths(cfg) -> dict:
    """
    Initialize all key paths from the provided config parser.

    Returns a dict with:
      - base_dir
      - run_dir
      - results_dir
      - download_folder
    """
    run_dir = get_run_dir()
    base_dir = get_base_dir()
    results_dir = get_results_dir(run_dir, cfg["PATHS"]["ResultsDir"])
    download_folder = get_download_folder(cfg["PATHS"]["DownloadFolder"], run_dir)
    return {
        'BASE_DIR': base_dir,
        'RUN_DIR': run_dir,
        'RESULTS_DIR': results_dir,
        'DOWNLOAD_FOLDER': download_folder,
    }
