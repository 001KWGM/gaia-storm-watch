from pathlib import Path
import yaml
from .paths import CONFIG_DIR


def load_yaml(name: str) -> dict:
    path = CONFIG_DIR / name
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_hubs() -> dict:
    return load_yaml("hubs.yaml")


def load_sources() -> dict:
    return load_yaml("source_registry.yaml")


def load_thresholds() -> dict:
    return load_yaml("thresholds.yaml")
