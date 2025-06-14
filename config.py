# config.py
import os

from dotenv import load_dotenv

# look for .env in the project root
load_dotenv()

SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
SQLALCHEMY_TRACK_MODIFICATIONS = False
# Only one SECRET_KEY definition:
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY not set in .env")
