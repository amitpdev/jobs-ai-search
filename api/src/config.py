# LinkedAI api config
# ---
import os
import pathlib

from dotenv import load_dotenv

load_dotenv()
project_root = pathlib.Path(__file__).parent.parent.resolve()

UVICORN_LOGGING_LEVEL = "DEBUG"  # 'INFO' / 'WARNING' / 'ERROR' / 'DEBUG'
SQLITE_DB_FILE = project_root.parent / "data" / "linkedai.db"
ENDPOINT_NLU = os.environ.get("ENDPOINT_NLU", "http://localhost:5005/model/parse")
