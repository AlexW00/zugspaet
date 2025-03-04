import logging
import os
from pathlib import Path

# Environment settings
IS_PRODUCTION = os.getenv("PRODUCTION", "false").lower() == "true"
LOG_LEVEL = logging.WARNING if IS_PRODUCTION else logging.INFO

# API settings
API_KEY = os.getenv("API_KEY")
CLIENT_ID = os.getenv("CLIENT_ID")
PRIVATE_API_KEY = os.getenv("PRIVATE_API_KEY")
BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")

# Directory settings
EVA_DIR = Path(os.getenv("EVA_DIR", "data"))
XML_DIR = Path(os.getenv("XML_DIR", "data"))
LOGS_DIR = Path("logs")

# Rate limiting settings
RATE_LIMITS = {"default": ["2000 per day", "100 per hour"]}

# Database settings
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "deutsche_bahn_data")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")


# Validate required settings
def validate_settings():
    if not API_KEY:
        raise ValueError("No API Key provided!")
    if not CLIENT_ID:
        raise ValueError("No Client Id provided!")
    if not PRIVATE_API_KEY:
        raise ValueError("No Private API Key provided!")
    if not BASE_URL:
        raise ValueError("No Base URL provided!")
    if not EVA_DIR:
        raise ValueError("No eva directory provided!")
    if not XML_DIR:
        raise ValueError("No xml directory provided!")


# Create necessary directories
def create_directories():
    LOGS_DIR.mkdir(exist_ok=True)
    EVA_DIR.mkdir(exist_ok=True)
    XML_DIR.mkdir(exist_ok=True)
