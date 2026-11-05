import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", override=True)


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "").replace(
        "postgresql://",
        "postgresql+psycopg2://",
        1
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_ALGORITHM = "RS256"
    JWT_DECODE_ALGORITHMS = ["RS256"]

    JWT_PUBLIC_KEY = os.getenv("JWT_PUBLIC_KEY")

    if not JWT_PUBLIC_KEY:
        public_key_path = BASE_DIR / "keys" / "public_key.pem"
        if public_key_path.exists():
            JWT_PUBLIC_KEY = public_key_path.read_text(encoding="utf-8")

    SERVER_C_URL = os.getenv("SERVER_C_URL")
    SERVER_C_API_KEY = os.getenv("SERVER_C_API_KEY")