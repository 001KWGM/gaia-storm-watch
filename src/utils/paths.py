from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
ARCHIVE_DIR = DATA_DIR / "archive"
EXPORT_DIR = ROOT / "exports"

for path in [PROCESSED_DIR, ARCHIVE_DIR, EXPORT_DIR / "public_summary", EXPORT_DIR / "internal_logs"]:
    path.mkdir(parents=True, exist_ok=True)
