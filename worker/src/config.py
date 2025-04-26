# LinkedAI worker config
# ---
import os
import pathlib

from dotenv import load_dotenv

load_dotenv()
project_root = pathlib.Path(__file__).parent.parent.resolve()

# Endpoints
CELERY_BACKEND = os.environ.get("CELERY_BACKEND", "redis://localhost:6379/0")
OUTPUT_API = os.environ.get("JOBS_API_ENDPOINT", "http://127.0.0.1:8000/jobs")
OUTPUT_CSV = ""

# Scraping related
PARSE_DEBUG = False
SELENIUM_HEADLESS = False
SELENIUM_LOCAL_CHROME = True
COOKIEJAR_FILENAME = project_root.parent / "data" / "cookiejar.dump"
RESULTS_DIR = project_root.parent / "data" / "results"

SELENIUM_REMOTE_ENDPOINT = os.environ.get(
    "SELENIUM_REMOTE_ENDPOINT", "http://localhost:4444"
)
LINKEDIN_USERNAME = os.environ.get("LINKEDIN_USERNAME", "")
LINKEDIN_PASSWORD = os.environ.get("LINKEDIN_PASSWORD", "")
LINKEDIN_QUERY_STRING = os.environ.get("LINKEDIN_QUERY_STRING", "")
LINKEDIN_QUERY_LOCATION = os.environ.get("LINKEDIN_QUERY_LOCATION", "")
LINKEDIN_SCRAPE_MAX_PAGES = os.environ.get("LINKEDIN_MAX_SCRAPE_PAGES", 1)
