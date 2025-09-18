# utils/config.py
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, MutableMapping, Optional

class ConfigError(Exception):
    """Custom exception for configuration validation errors."""
    pass


class _Section(MutableMapping[str, Any]):
    """
    Case-insensitive dict-like view over a single section.
    Provides .get(...) like dict and can be indexed case-insensitively.
    """
    def __init__(self, data: Dict[str, Any]):
        # internal keys are already UPPERCASE
        self._data = data

    # Mapping protocol
    def __getitem__(self, key: str) -> Any:
        return self._data[key.upper()]

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key.upper()] = value

    def __delitem__(self, key: str) -> None:
        del self._data[key.upper()]

    def __iter__(self):
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    # helpers
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        return self._data.get(key.upper(), default)

    def getboolean(self, key: str, default: Optional[bool] = None) -> bool:
        val = self.get(key, default)
        if isinstance(val, bool):
            return val
        if val is None:
            return bool(default) if default is not None else False
        s = str(val).strip().lower()
        if s in ('1', 'true', 'yes', 'y', 'on'):
            return True
        if s in ('0', 'false', 'no', 'n', 'off'):
            return False
        # fallback: truthy if non-empty
        return bool(s)

    def getint(self, key: str, default: Optional[int] = None) -> int:
        val = self.get(key, default)
        try:
            return int(val)
        except Exception:
            if default is not None:
                return int(default)
            raise

    def getfloat(self, key: str, default: Optional[float] = None) -> float:
        val = self.get(key, default)
        try:
            return float(val)
        except Exception:
            if default is not None:
                return float(default)
            raise


class Config(MutableMapping[str, _Section]):
    """
    A thin wrapper that behaves like configparser.ConfigParser for read access,
    backed by a nested dict loaded from JSON. Sections and keys are case-insensitive.
    """
    def __init__(self, data: Dict[str, Dict[str, Any]]):
        # normalize sections/keys to UPPERCASE for stable access
        self._data: Dict[str, Dict[str, Any]] = {
            str(sec).upper(): {str(k).upper(): v for k, v in (vals or {}).items()}
            for sec, vals in (data or {}).items()
        }

    # Mapping protocol for top-level sections
    def __getitem__(self, section: str) -> _Section:
        return _Section(self._data[section.upper()])

    def __setitem__(self, section: str, value: Dict[str, Any]) -> None:
        self._data[section.upper()] = {str(k).upper(): v for k, v in value.items()}

    def __delitem__(self, section: str) -> None:
        del self._data[section.upper()]

    def __iter__(self):
        # iterate section names
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def get(self, section: str, key: str, fallback: Optional[Any] = None) -> Any:
        return self._data.get(section.upper(), {}).get(key.upper(), fallback)

    def getboolean(self, section: str, key: str, fallback: Optional[bool] = None) -> bool:
        return self[section].getboolean(key, fallback)

    def sections(self) -> Iterable[str]:
        return list(self._data.keys())

    def __contains__(self, section: str) -> bool:
        return section.upper() in self._data


# ---- Loader / Validator -------------------------------------------------

DEFAULT_CONFIG_NAME = "config.json"

_REQUIRED_SECTIONS = [
    "USER",
    "PATHS",
    "SHAPEFILES",
    "COLORS",
    "WEIGHTS",
    "OPACITIES",
    "LEGEND",
]

_REQUIRED_KEYS = {
    "USER": ["NAME", "EMAIL"],
    "PATHS": ["DOWNLOADFOLDER", "RESULTSDIR"],
    "SHAPEFILES": ["CONDUIT", "FIBERCABLE", "STRUCTURE"],
    # the rest have reasonable defaults in code paths, so individual keys are optional
}

def _coerce_env_and_expand(val: Any) -> Any:
    if isinstance(val, str):
        # expand ~ and %VAR% / $VAR
        val = os.path.expanduser(val)
        val = os.path.expandvars(val)
    return val

def _postprocess_paths(cfg_dict: Dict[str, Dict[str, Any]]) -> None:
    # Ensure PATHS keys are present with canonical names
    paths = cfg_dict.setdefault("PATHS", {})
    # normalize common variants from older files
    aliases = {
        "DOWNLOADFOLDER": ["DOWNLOAD_DIR", "DOWNLOADFOLDER", "DOWNLOADFOLDERPATH", "DOWNLOADPATH"],
        "RESULTSDIR":     ["RESULTS_DIR", "RESULTSDIR", "RESULTSPATH"],
        "PYTHONEXE":      ["PYTHON", "PYTHONEXE", "PYTHON_PATH"],
        "SCRIPTPATH":     ["SCRIPT", "SCRIPTPATH", "ENTRYPOINT"],
    }
    normalized = {}
    for canon, alts in aliases.items():
        for k in alts:
            if k in paths:
                normalized[canon] = paths[k]
                break
    # Also map lowercase keys from JSON if present (already uppercased in __init__)
    for canon in aliases:
        if canon not in normalized and canon in paths:
            normalized[canon] = paths[canon]
    # write back
    paths.update(normalized)
    # expand any env tokens and ~
    for k in list(paths.keys()):
        paths[k] = _coerce_env_and_expand(paths[k])

def _validate(cfg: Config) -> None:
    missing_sections = [s for s in _REQUIRED_SECTIONS if s not in cfg]
    if missing_sections:
        raise ConfigError(f"Invalid configuration: missing required sections: {', '.join(missing_sections)}")

    key_errors = []
    for sec, keys in _REQUIRED_KEYS.items():
        if sec not in cfg:
            continue
        for k in keys:
            v = cfg[sec].get(k, None)
            if v is None or (isinstance(v, str) and str(v).strip() == ""):
                key_errors.append(f"{sec}.{k}")
    if key_errors:
        raise ConfigError("Invalid configuration: missing or empty keys -> " + ", ".join(key_errors))

def _search_default_config() -> Path:
    """
    Look for config.json in a few common places:
      - repo_root/config.json
      - repo_root/Setup/config.json
      - current working directory/config.json
    """
    # utils/ is under repo_root/utils/...
    here = Path(__file__).resolve()
    repo_root = here.parents[1] if len(here.parents) >= 2 else Path.cwd()
    candidates = [
        repo_root / "config.json",
        repo_root / "Setup" / "config.json",
        Path.cwd() / "config.json",
    ]
    for p in candidates:
        if p.exists():
            return p
    # fallback: default name in cwd (allows overrides)
    return Path(DEFAULT_CONFIG_NAME)

def load_config(path: Path) -> Config:
    """
    Load a JSON-based configuration file and return a Config wrapper.

    Args:
        path: Path to a JSON file.

    Returns:
        Config: mapping-like object with case-insensitive section/key access.

    Raises:
        ConfigError if the file can't be read or is invalid.
    """
    p = Path(path)
    if not p.exists():
        raise ConfigError(f"Configuration file not found: {p}")

    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        raise ConfigError(f"Failed to parse JSON from {p}: {e}")

    cfg = Config(raw)
    _postprocess_paths(cfg._data)
    _validate(cfg)
    return cfg

def load_default_config() -> Config:
    """
    Find and load the default config.json.
    """
    return load_config(_search_default_config())
