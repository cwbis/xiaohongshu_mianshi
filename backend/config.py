from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT / "dist"
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "offerscope.db"
SCHEMA_VERSION = 3
DEFAULT_PORT = 8080
XHS_SCRIPT_DIR = ROOT / "XhsSkills-master" / "skills" / "xhs-apis" / "scripts"

SUPPORTED_SETTING_SCOPES = {"xhsConfig", "llmConfig"}
