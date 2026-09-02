import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
DB_PATH = os.getenv("EDITH_DB_PATH", str(BASE_DIR / "edith.db"))
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")