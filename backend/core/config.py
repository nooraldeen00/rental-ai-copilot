# backend/core/config.py
import os
from dotenv import load_dotenv

# Load .env from repo root
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not set. Add it to your .env in the repo root.")
