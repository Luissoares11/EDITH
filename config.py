import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
DB_PATH = Path(os.getenv("EDITH_DB_PATH", BASE_DIR / "data" / "edith.db"))
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
